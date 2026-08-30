import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from ai.domain.types import LLMResponse
from ai.orchestrator import ChatOrchestrator
from conversations.models import Conversation, Message
from ai.domain.exceptions import LLMProviderError

User = get_user_model()


class FakeGateway:
    def generate(self, messages):
        return LLMResponse(
            content="Fake AI response",
            model="fake-model",
            provider="fake",
            usage=None,
            finish_reason="stop",
        )


@pytest.fixture
def user():
    return User.objects.create_user(
        username="message_user",
        password="StrongPassword123!",
    )


@pytest.fixture
def authenticated_client(user):
    client = APIClient()

    response = client.post(
        "/api/auth/token/",
        {
            "username": "message_user",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 200

    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
    )

    return client


@pytest.fixture
def conversation(user):
    return Conversation.objects.create(
        user=user,
        title="Test Conversation",
    )


@pytest.fixture
def fake_orchestrator(monkeypatch):
    monkeypatch.setattr(
        "conversations.views.ChatOrchestrator",
        lambda: ChatOrchestrator(
            gateway=FakeGateway(),
        ),
    )


@pytest.mark.django_db
def test_authenticated_user_can_create_message(
    authenticated_client,
    conversation,
    fake_orchestrator,
):
    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "content": "What is RAG?",
        },
        format="json",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["role"] == Message.Role.ASSISTANT
    assert data["content"] == "Fake AI response"
    assert "id" in data
    assert "created_at" in data

    user_message = Message.objects.get(
        conversation=conversation,
        role=Message.Role.USER,
    )

    assert user_message.content == "What is RAG?"

    assistant_message = Message.objects.get(
        id=data["id"],
    )

    assert assistant_message.conversation == conversation
    assert assistant_message.role == Message.Role.ASSISTANT
    assert assistant_message.content == "Fake AI response"


@pytest.mark.django_db
def test_message_role_cannot_be_spoofed(
    authenticated_client,
    conversation,
    fake_orchestrator,
):
    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "role": "assistant",
            "content": "Fake assistant message",
        },
        format="json",
    )

    assert response.status_code == 201

    data = response.json()

    # The client-supplied role must be ignored.
    assert data["role"] == Message.Role.ASSISTANT
    assert data["content"] == "Fake AI response"

    user_message = Message.objects.get(
        conversation=conversation,
        role=Message.Role.USER,
    )

    assert user_message.content == "Fake assistant message"


@pytest.mark.django_db
def test_authenticated_user_can_list_messages(
    authenticated_client,
    conversation,
):
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content="First message",
    )

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content="Second message",
    )

    response = authenticated_client.get(
        f"/api/conversations/{conversation.id}/messages/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["content"] == "First message"
    assert data[1]["content"] == "Second message"


@pytest.mark.django_db
def test_user_cannot_access_another_users_messages(
    authenticated_client,
):
    other_user = User.objects.create_user(
        username="other_message_user",
        password="StrongPassword123!",
    )

    other_conversation = Conversation.objects.create(
        user=other_user,
        title="Private Conversation",
    )

    Message.objects.create(
        conversation=other_conversation,
        role=Message.Role.USER,
        content="Private message",
    )

    response = authenticated_client.get(
        f"/api/conversations/{other_conversation.id}/messages/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_create_message_in_another_users_conversation(
    authenticated_client,
    fake_orchestrator,
):
    other_user = User.objects.create_user(
        username="other_create_user",
        password="StrongPassword123!",
    )

    other_conversation = Conversation.objects.create(
        user=other_user,
        title="Private Conversation",
    )

    response = authenticated_client.post(
        f"/api/conversations/{other_conversation.id}/messages/",
        {
            "content": "Unauthorized message",
        },
        format="json",
    )

    assert response.status_code == 404

    assert not Message.objects.filter(
        conversation=other_conversation,
        content="Unauthorized message",
    ).exists()


@pytest.mark.django_db
def test_unauthenticated_user_cannot_list_messages(
    conversation,
):
    client = APIClient()

    response = client.get(
        f"/api/conversations/{conversation.id}/messages/"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_unauthenticated_user_cannot_create_message(
    conversation,
):
    client = APIClient()

    response = client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "content": "Unauthorized",
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_message_requires_content(
    authenticated_client,
    conversation,
):
    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_message_empty_content_is_rejected(
    authenticated_client,
    conversation,
):
    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "content": "",
        },
        format="json",
    )

    assert response.status_code == 400

@pytest.mark.django_db
def test_llm_provider_error_returns_safe_api_response(
    authenticated_client,
    conversation,
    monkeypatch,
):
    class FailingOrchestrator:
        def chat(self, *, conversation, content):
            raise LLMProviderError(
                "FreeLLMAPI connection failed internally"
            )

    monkeypatch.setattr(
        "conversations.views.ChatOrchestrator",
        FailingOrchestrator,
    )

    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "content": "Hello AI",
        },
        format="json",
    )

    assert response.status_code == 503

    data = response.json()

    assert data == {
        "detail": "The AI service is temporarily unavailable."
    }

    assert "FreeLLMAPI" not in str(data)

@pytest.mark.django_db
def test_llm_timeout_returns_gateway_timeout(
    authenticated_client,
    conversation,
    monkeypatch,
):
    from ai.domain.exceptions import LLMTimeoutError

    class FailingOrchestrator:
        def chat(self, *, conversation, content):
            raise LLMTimeoutError(
                "Provider timed out after 30 seconds"
            )

    monkeypatch.setattr(
        "conversations.views.ChatOrchestrator",
        FailingOrchestrator,
    )

    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "content": "Hello AI",
        },
        format="json",
    )

    assert response.status_code == 504

    assert response.json() == {
        "detail": "The AI service timed out."
    }

@pytest.mark.django_db
def test_llm_rate_limit_returns_429(
    authenticated_client,
    conversation,
    monkeypatch,
):
    from ai.domain.exceptions import LLMRateLimitError

    class FailingOrchestrator:
        def chat(self, *, conversation, content):
            raise LLMRateLimitError(
                "Provider rate limit exceeded"
            )

    monkeypatch.setattr(
        "conversations.views.ChatOrchestrator",
        FailingOrchestrator,
    )

    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "content": "Hello AI",
        },
        format="json",
    )

    assert response.status_code == 429

    assert response.json() == {
        "detail": "The AI service is temporarily rate limited."
    }

@pytest.mark.django_db
def test_llm_failure_preserves_user_message_and_creates_no_assistant(
    authenticated_client,
    conversation,
    monkeypatch,
):
    class FailingOrchestrator:
        def chat(self, *, conversation, content):
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.USER,
                content=content,
            )

            raise LLMProviderError(
                "FreeLLMAPI connection failed internally"
            )

    monkeypatch.setattr(
        "conversations.views.ChatOrchestrator",
        FailingOrchestrator,
    )

    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {
            "content": "This message must survive the failure",
        },
        format="json",
    )

    assert response.status_code == 503

    assert Message.objects.filter(
        conversation=conversation,
        role=Message.Role.USER,
        content="This message must survive the failure",
    ).exists()

    assert not Message.objects.filter(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
    ).exists()
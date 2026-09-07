import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from conversations.models import Conversation

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        username="stream_user",
        password="StrongPassword123!",
    )


@pytest.fixture
def authenticated_client(user):
    client = APIClient()

    response = client.post(
        "/api/auth/token/",
        {
            "username": "stream_user",
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
        title="Streaming Test",
    )


@pytest.mark.django_db
def test_streaming_message_passes_selected_model_to_orchestrator(
    authenticated_client,
    conversation,
    monkeypatch,
):
    captured = {}

    class FakeOrchestrator:
        def __init__(self, model=None):
            captured["model"] = model

        def chat_stream(self, *, conversation, content):
            yield {
                "type": "done",
                "message": {},
                "sources": [],
                "mode": "general",
            }

    monkeypatch.setattr(
        "conversations.views.ChatOrchestrator",
        FakeOrchestrator,
    )

    response = authenticated_client.post(
        f"/api/conversations/{conversation.id}/messages/stream/",
        {
            "content": "Explain RAG",
            "model": "gemini-3.6-flash",
        },
        format="json",
    )

    assert response.status_code == 200

    list(response.streaming_content)

    assert captured["model"] == "gemini-3.6-flash"

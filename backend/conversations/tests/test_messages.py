import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from conversations.models import Conversation, Message


User = get_user_model()


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


@pytest.mark.django_db
def test_authenticated_user_can_create_message(
    authenticated_client,
    conversation,
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

    assert data["role"] == "user"
    assert data["content"] == "What is RAG?"
    assert "id" in data
    assert "created_at" in data

    message = Message.objects.get(id=data["id"])

    assert message.conversation == conversation
    assert message.role == Message.Role.USER


@pytest.mark.django_db
def test_message_role_cannot_be_spoofed(
    authenticated_client,
    conversation,
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

    assert data["role"] == Message.Role.USER

    message = Message.objects.get(id=data["id"])

    assert message.role == Message.Role.USER


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
def test_message_empty_content_behavior(
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
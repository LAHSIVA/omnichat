import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        username="testuser",
        password="StrongPassword123!",
    )


@pytest.fixture
def authenticated_client(user):
    client = APIClient()
    response = client.post(
        "/api/auth/token/",
        {
            "username": "testuser",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
    )

    return client


@pytest.mark.django_db
def test_unauthenticated_user_cannot_list_conversations():
    client = APIClient()

    response = client.get("/api/conversations/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_user_can_create_conversation(authenticated_client, user):
    response = authenticated_client.post(
        "/api/conversations/",
        {"title": "Learning RAG"},
        format="json",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Learning RAG"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    conversation = user.conversations.get()

    assert conversation.title == "Learning RAG"
    assert conversation.user == user


@pytest.mark.django_db
def test_user_can_list_own_conversations(authenticated_client, user):
    user.conversations.create(title="Conversation One")
    user.conversations.create(title="Conversation Two")

    response = authenticated_client.get("/api/conversations/")

    assert response.status_code == 200

    titles = {item["title"] for item in response.json()}

    assert titles == {
        "Conversation One",
        "Conversation Two",
    }


@pytest.mark.django_db
def test_user_cannot_see_another_users_conversation(
    authenticated_client,
):
    other_user = User.objects.create_user(
        username="otheruser",
        password="StrongPassword123!",
    )

    conversation = other_user.conversations.create(
        title="Private Conversation",
    )

    response = authenticated_client.get(
        f"/api/conversations/{conversation.id}/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_can_update_own_conversation(
    authenticated_client,
    user,
):
    conversation = user.conversations.create(
        title="Old Title",
    )

    response = authenticated_client.patch(
        f"/api/conversations/{conversation.id}/",
        {"title": "New Title"},
        format="json",
    )

    assert response.status_code == 200

    conversation.refresh_from_db()

    assert conversation.title == "New Title"


@pytest.mark.django_db
def test_user_cannot_update_another_users_conversation(
    authenticated_client,
):
    other_user = User.objects.create_user(
        username="otheruser",
        password="StrongPassword123!",
    )

    conversation = other_user.conversations.create(
        title="Private Conversation",
    )

    response = authenticated_client.patch(
        f"/api/conversations/{conversation.id}/",
        {"title": "Hacked Title"},
        format="json",
    )

    assert response.status_code == 404

    conversation.refresh_from_db()

    assert conversation.title == "Private Conversation"


@pytest.mark.django_db
def test_user_can_delete_own_conversation(
    authenticated_client,
    user,
):
    conversation = user.conversations.create(
        title="Delete Me",
    )

    response = authenticated_client.delete(
        f"/api/conversations/{conversation.id}/"
    )

    assert response.status_code == 204

    assert not user.conversations.filter(
        id=conversation.id
    ).exists()


@pytest.mark.django_db
def test_user_cannot_delete_another_users_conversation(
    authenticated_client,
):
    other_user = User.objects.create_user(
        username="otheruser",
        password="StrongPassword123!",
    )

    conversation = other_user.conversations.create(
        title="Do Not Delete",
    )

    response = authenticated_client.delete(
        f"/api/conversations/{conversation.id}/"
    )

    assert response.status_code == 404

    assert other_user.conversations.filter(
        id=conversation.id
    ).exists()
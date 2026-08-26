import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_user_can_register():
    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "test@example.com"
    assert "password" not in response.json()


@pytest.mark.django_db
def test_password_is_hashed():
    client = APIClient()
    password = "StrongPassword123!"

    response = client.post(
        "/api/auth/register/",
        {
            "username": "hashuser",
            "email": "hash@example.com",
            "password": password,
        },
        format="json",
    )

    assert response.status_code == 201

    user = get_user_model().objects.get(username="hashuser")

    assert user.password != password
    assert user.check_password(password)


@pytest.mark.django_db
def test_duplicate_username_is_rejected():
    client = APIClient()

    payload = {
        "username": "duplicate",
        "email": "first@example.com",
        "password": "StrongPassword123!",
    }

    first_response = client.post(
        "/api/auth/register/",
        payload,
        format="json",
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/auth/register/",
        {
            **payload,
            "email": "second@example.com",
        },
        format="json",
    )

    assert second_response.status_code == 400


@pytest.mark.django_db
def test_weak_password_is_rejected():
    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "password",
        },
        format="json",
    )

    assert response.status_code == 400
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
)

User = get_user_model()


@pytest.fixture
def user():
    """Create a user for authentication tests."""
    return User.objects.create_user(
        username="authuser",
        email="auth@example.com",
        password="StrongPassword123!",
    )


@pytest.mark.django_db
def test_user_can_login(user):
    """A valid user should receive access and refresh tokens."""
    client = APIClient()

    response = client.post(
        "/api/auth/token/",
        {
            "username": "authuser",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 200

    data = response.json()

    assert "access" in data
    assert "refresh" in data

    assert data["access"]
    assert data["refresh"]


@pytest.mark.django_db
def test_wrong_password_is_rejected(user):
    """Invalid credentials should be rejected."""
    client = APIClient()

    response = client.post(
        "/api/auth/token/",
        {
            "username": "authuser",
            "password": "WrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_protected_endpoint_requires_authentication():
    """Protected endpoints should reject unauthenticated requests."""
    client = APIClient()

    response = client.get("/api/auth/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_user_can_access_me(user):
    """An authenticated user should access the current-user endpoint."""
    client = APIClient()

    login_response = client.post(
        "/api/auth/token/",
        {
            "username": "authuser",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access"]

    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

    response = client.get("/api/auth/me/")

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "username": "authuser",
        "email": "auth@example.com",
    }


@pytest.mark.django_db
def test_invalid_access_token_is_rejected():
    """Invalid JWTs should not authenticate requests."""
    client = APIClient()

    client.credentials(
        HTTP_AUTHORIZATION="Bearer invalid.jwt.token"
    )

    response = client.get("/api/auth/me/")

    assert response.status_code == 401

@pytest.mark.django_db
def test_refresh_token_rotation(user):
    """Refreshing should rotate the refresh token."""
    client = APIClient()

    login_response = client.post(
        "/api/auth/token/",
        {
            "username": "authuser",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    assert login_response.status_code == 200

    old_refresh_token = login_response.json()["refresh"]

    refresh_response = client.post(
        "/api/auth/token/refresh/",
        {
            "refresh": old_refresh_token,
        },
        format="json",
    )

    assert refresh_response.status_code == 200

    data = refresh_response.json()

    assert "access" in data
    assert "refresh" in data

    new_refresh_token = data["refresh"]

    assert new_refresh_token != old_refresh_token

@pytest.mark.django_db
def test_old_refresh_token_is_blacklisted_after_rotation(user):
    """A rotated refresh token should no longer be usable."""
    client = APIClient()

    login_response = client.post(
        "/api/auth/token/",
        {
            "username": "authuser",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    old_refresh_token = login_response.json()["refresh"]

    refresh_response = client.post(
        "/api/auth/token/refresh/",
        {
            "refresh": old_refresh_token,
        },
        format="json",
    )

    assert refresh_response.status_code == 200

    reuse_response = client.post(
        "/api/auth/token/refresh/",
        {
            "refresh": old_refresh_token,
        },
        format="json",
    )

    assert reuse_response.status_code == 401

@pytest.mark.django_db
def test_logout_blacklists_refresh_token(user):
    """Logging out should blacklist the refresh token."""
    client = APIClient()

    login_response = client.post(
        "/api/auth/token/",
        {
            "username": "authuser",
            "password": "StrongPassword123!",
        },
        format="json",
    )

    refresh_token = login_response.json()["refresh"]

    logout_response = client.post(
        "/api/auth/logout/",
        {
            "refresh": refresh_token,
        },
        format="json",
    )

    assert logout_response.status_code == 200

    refresh_response = client.post(
        "/api/auth/token/refresh/",
        {
            "refresh": refresh_token,
        },
        format="json",
    )

    assert refresh_response.status_code == 401
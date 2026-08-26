import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoint():
    """Health endpoint should be publicly accessible."""
    client = APIClient()

    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
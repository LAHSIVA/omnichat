import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from unittest.mock import patch
from knowledge.models import Document


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="knowledgeuser",
        password="StrongPassword123!",
    )


@pytest.fixture
def authenticated_client(user):
    client = APIClient()

    response = client.post(
        "/api/auth/token/",
        {
            "username": "knowledgeuser",
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
def uploaded_file():
    return SimpleUploadedFile(
        "notes.txt",
        b"Machine learning notes.",
        content_type="text/plain",
    )


@pytest.mark.django_db
def test_authenticated_user_can_upload_document(
    authenticated_client,
    user,
    uploaded_file,
):
    response = authenticated_client.post(
        "/api/knowledge/documents/",
        {
            "title": "Machine Learning Notes",
            "file": uploaded_file,
        },
        format="multipart",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Machine Learning Notes"
    assert data["original_filename"] == "notes.txt"
    assert data["content_type"] == "text/plain"
    assert data["status"] == Document.Status.PENDING

    document = Document.objects.get(
        id=data["id"],
    )

    assert document.user == user

@pytest.mark.django_db
def test_unauthenticated_user_cannot_upload_document(
    uploaded_file,
):
    client = APIClient()

    response = client.post(
        "/api/knowledge/documents/",
        {
            "title": "Unauthorized Document",
            "file": uploaded_file,
        },
        format="multipart",
    )

    assert response.status_code == 401

    assert not Document.objects.filter(
        title="Unauthorized Document",
    ).exists()

@pytest.mark.django_db
def test_user_can_only_list_their_own_documents(
    authenticated_client,
    user,
):
    other_user = user.__class__.objects.create_user(
        username="otherknowledgeuser",
        password="StrongPassword123!",
    )

    own_document = Document.objects.create(
        user=user,
        title="My Document",
        original_filename="mine.txt",
        content_type="text/plain",
    )

    Document.objects.create(
        user=other_user,
        title="Private Other Document",
        original_filename="private.txt",
        content_type="text/plain",
    )

    response = authenticated_client.get(
        "/api/knowledge/documents/",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == own_document.id
    assert data[0]["title"] == "My Document"

@pytest.mark.django_db
def test_user_cannot_retrieve_another_users_document(
    authenticated_client,
    user,
):
    other_user = user.__class__.objects.create_user(
        username="detailotheruser",
        password="StrongPassword123!",
    )

    other_document = Document.objects.create(
        user=other_user,
        title="Private Document",
        original_filename="private.txt",
        content_type="text/plain",
    )

    response = authenticated_client.get(
        f"/api/knowledge/documents/{other_document.id}/",
    )

    assert response.status_code == 404

@pytest.mark.django_db
def test_user_can_retrieve_their_own_document(
    authenticated_client,
    user,
):
    document = Document.objects.create(
        user=user,
        title="My Private Notes",
        original_filename="notes.txt",
        content_type="text/plain",
    )

    response = authenticated_client.get(
        f"/api/knowledge/documents/{document.id}/",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == document.id
    assert data["title"] == "My Private Notes"
    assert data["original_filename"] == "notes.txt"
    assert data["content_type"] == "text/plain"
    assert data["status"] == Document.Status.PENDING

@pytest.mark.django_db
def test_document_upload_rejects_unsupported_file_type(
    authenticated_client,
):
    uploaded_file = SimpleUploadedFile(
        "malware.exe",
        b"not really an executable",
        content_type="application/octet-stream",
    )

    response = authenticated_client.post(
        "/api/knowledge/documents/",
        {
            "title": "Unsupported File",
            "file": uploaded_file,
        },
        format="multipart",
    )

    assert response.status_code == 400

    assert not Document.objects.filter(
        title="Unsupported File",
    ).exists()

@pytest.mark.django_db
def test_document_upload_rejects_file_over_size_limit(
    authenticated_client,
):
    oversized_content = b"x" * (10 * 1024 * 1024 + 1)

    uploaded_file = SimpleUploadedFile(
        "large.txt",
        oversized_content,
        content_type="text/plain",
    )

    response = authenticated_client.post(
        "/api/knowledge/documents/",
        {
            "title": "Large Document",
            "file": uploaded_file,
        },
        format="multipart",
    )

    assert response.status_code == 400

    assert not Document.objects.filter(
        title="Large Document",
    ).exists()

@pytest.mark.django_db
def test_document_upload_requires_file(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/knowledge/documents/",
        {
            "title": "Document Without File",
        },
        format="multipart",
    )

    assert response.status_code == 400

    assert not Document.objects.filter(
        title="Document Without File",
    ).exists()

@pytest.mark.django_db
def test_document_upload_dispatches_processing_task(
    authenticated_client,
    uploaded_file,
):
    with patch(
        "knowledge.views.process_document_task.delay"
    ) as mock_task:
        response = authenticated_client.post(
            "/api/knowledge/documents/",
            {
                "title": "Task Dispatch Test",
                "file": uploaded_file,
            },
            format="multipart",
        )

    assert response.status_code == 201

    document = Document.objects.get(
        id=response.json()["id"]
    )

    mock_task.assert_called_once_with(document.id)


@pytest.mark.django_db
def test_user_can_delete_their_own_document(
    authenticated_client,
    user,
):
    document = Document.objects.create(
        user=user,
        title="Document To Delete",
        original_filename="delete.txt",
        content_type="text/plain",
    )

    response = authenticated_client.delete(
        f"/api/knowledge/documents/{document.id}/"
    )

    assert response.status_code == 204

    assert not Document.objects.filter(
        id=document.id,
    ).exists()

@pytest.mark.django_db
def test_user_cannot_delete_another_users_document(
    authenticated_client,
    user,
):
    other_user = user.__class__.objects.create_user(
        username="deleteotheruser",
        password="StrongPassword123!",
    )

    document = Document.objects.create(
        user=other_user,
        title="Private Document",
        original_filename="private.txt",
        content_type="text/plain",
    )

    response = authenticated_client.delete(
        f"/api/knowledge/documents/{document.id}/"
    )

    assert response.status_code == 404

    assert Document.objects.filter(
        id=document.id,
    ).exists()

@pytest.mark.django_db
def test_user_can_retry_failed_document(
    authenticated_client,
    user,
):
    document = Document.objects.create(
        user=user,
        title="Failed Document",
        original_filename="failed.txt",
        content_type="text/plain",
        status=Document.Status.FAILED,
    )

    with patch(
        "knowledge.views.process_document_task.delay"
    ) as mock_task:
        response = authenticated_client.post(
            f"/api/knowledge/documents/{document.id}/retry/"
        )

    assert response.status_code == 202

    document.refresh_from_db()

    assert document.status == Document.Status.PENDING

    mock_task.assert_called_once_with(document.id)

@pytest.mark.django_db
def test_user_cannot_retry_another_users_document(
    authenticated_client,
    user,
):
    other_user = user.__class__.objects.create_user(
        username="retryotheruser",
        password="StrongPassword123!",
    )

    document = Document.objects.create(
        user=other_user,
        title="Private Failed Document",
        original_filename="private.txt",
        content_type="text/plain",
        status=Document.Status.FAILED,
    )

    with patch(
        "knowledge.views.process_document_task.delay"
    ) as mock_task:
        response = authenticated_client.post(
            f"/api/knowledge/documents/{document.id}/retry/"
        )

    assert response.status_code == 404

    mock_task.assert_not_called()

@pytest.mark.django_db
def test_completed_document_cannot_be_retried(
    authenticated_client,
    user,
):
    document = Document.objects.create(
        user=user,
        title="Completed Document",
        original_filename="completed.txt",
        content_type="text/plain",
        status=Document.Status.COMPLETED,
    )

    with patch(
        "knowledge.views.process_document_task.delay"
    ) as mock_task:
        response = authenticated_client.post(
            f"/api/knowledge/documents/{document.id}/retry/"
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Only failed documents can be retried."
    )

    mock_task.assert_not_called()
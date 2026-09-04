import pytest
from django.core.files.base import ContentFile

from knowledge.embeddings import FakeEmbeddingProvider
from knowledge.models import Document
from knowledge.processing import process_document
from knowledge.services import DocumentProcessingService


@pytest.mark.django_db
def test_process_document_processes_document(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="processingentryuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Processing Entry Test",
        original_filename="notes.txt",
        content_type="text/plain",
    )

    document.file.save(
        "notes.txt",
        ContentFile(
            b"Machine learning is useful."
        ),
    )

    processing_service = DocumentProcessingService(
        embedding_provider=FakeEmbeddingProvider(),
    )

    result = process_document(
        document.id,
        processing_service=processing_service,
    )

    document.refresh_from_db()

    assert result == "Machine learning is useful."
    assert document.status == Document.Status.COMPLETED
    assert document.extracted_text == "Machine learning is useful."

@pytest.mark.django_db
def test_process_document_raises_for_missing_document():
    with pytest.raises(Document.DoesNotExist):
        process_document(999999)

@pytest.mark.django_db
def test_failed_processing_rolls_back_chunks(
    django_user_model,
):
    from knowledge.models import DocumentChunk

    user = django_user_model.objects.create_user(
        username="rollbackuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Rollback Test",
        original_filename="notes.txt",
        content_type="text/plain",
    )

    document.file.save(
        "notes.txt",
        ContentFile(
            b"Machine learning is useful."
        ),
    )

    class FailingEmbeddingProvider:
        def embed(self, texts):
            raise RuntimeError("Embedding failed")

    processing_service = DocumentProcessingService(
        embedding_provider=FailingEmbeddingProvider(),
    )

    with pytest.raises(
        RuntimeError,
        match="Embedding failed",
    ):
        process_document(
            document.id,
            processing_service=processing_service,
        )

    document.refresh_from_db()

    assert document.status == Document.Status.FAILED

    assert not DocumentChunk.objects.filter(
        document=document,
    ).exists()
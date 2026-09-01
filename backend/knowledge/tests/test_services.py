from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile

from knowledge.extractors import UnsupportedDocumentTypeError
from knowledge.models import Document, DocumentChunk
from knowledge.services import DocumentProcessingService
from knowledge.search_service import DocumentSearchService
from knowledge.embeddings import FakeEmbeddingProvider

@pytest.mark.django_db
def test_document_processing_marks_document_completed(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="processinguser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Processing Test",
        original_filename="notes.txt",
        content_type="text/plain",
    )

    document.file.save(
        "notes.txt",
        ContentFile(
            b"Machine learning is useful."
        ),
    )

    service = DocumentProcessingService(
    embedding_provider=FakeEmbeddingProvider(),
    )

    text = service.process(document)

    document.refresh_from_db()

    assert text == "Machine learning is useful."
    assert document.status == Document.Status.COMPLETED
    assert document.extracted_text == "Machine learning is useful."


@pytest.mark.django_db
def test_document_processing_marks_document_failed_when_extraction_fails(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="failedprocessinguser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Failed Processing Test",
        original_filename="notes.txt",
        content_type="text/plain",
    )

    document.file.save(
        "notes.txt",
        ContentFile(b"Some content"),
    )

    service = DocumentProcessingService(
    embedding_provider=FakeEmbeddingProvider(),
    )

    error = UnsupportedDocumentTypeError(
        "Unsupported document type"
    )

    with patch(
        "knowledge.services.DocumentExtractorFactory.get_extractor",
        side_effect=error,
    ):
        with pytest.raises(
            UnsupportedDocumentTypeError,
            match="Unsupported document type",
        ):
            service.process(document)

    document.refresh_from_db()

    assert document.status == Document.Status.FAILED
    assert document.extracted_text == ""

@pytest.mark.django_db
def test_document_processing_creates_chunks(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="processingchunkuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Processing Chunk Test",
        original_filename="notes.txt",
        content_type="text/plain",
    )

    document.file.save(
        "notes.txt",
        ContentFile(
            (
                "This is a sufficiently long document "
                "that should be processed and converted "
                "into one or more document chunks."
            ).encode("utf-8")
        ),
    )

    service = DocumentProcessingService(
    embedding_provider=FakeEmbeddingProvider(),
    )

    service.process(document)

    document.refresh_from_db()

    chunks = list(
        DocumentChunk.objects.filter(
            document=document,
        ).order_by("chunk_index")
    )

    assert document.status == Document.Status.COMPLETED
    assert document.extracted_text
    assert len(chunks) > 0

    assert chunks[0].chunk_index == 0

    assert all(
        chunk.content
        for chunk in chunks
    )

@pytest.mark.django_db
def test_search_only_returns_chunks_belonging_to_user(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="searchowner",
        password="test-password-123",
    )

    other_user = django_user_model.objects.create_user(
        username="othersearchuser",
        password="test-password-123",
    )

    user_document = Document.objects.create(
        user=user,
        title="User Document",
        original_filename="user.txt",
        content_type="text/plain",
    )

    other_document = Document.objects.create(
        user=other_user,
        title="Other User Document",
        original_filename="other.txt",
        content_type="text/plain",
    )

    embedding = [1.0] + [0.0] * 1023

    DocumentChunk.objects.create(
        document=user_document,
        content="Private user content.",
        chunk_index=0,
        embedding=embedding,
    )

    DocumentChunk.objects.create(
        document=other_document,
        content="Private other user content.",
        chunk_index=0,
        embedding=embedding,
    )

    service = DocumentSearchService()

    results = service.search(
        query_embedding=embedding,
        user=user,
        limit=10,
    )

    assert len(results) == 1
    assert results[0].content == "Private user content."


@pytest.mark.django_db
def test_search_respects_limit(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="limitsearchuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Limit Test",
        original_filename="limit.txt",
        content_type="text/plain",
    )

    for index in range(5):
        DocumentChunk.objects.create(
            document=document,
            content=f"Chunk {index}",
            chunk_index=index,
            embedding=[1.0] + [0.0] * 1023,
        )

    service = DocumentSearchService()

    results = service.search(
        query_embedding=[1.0] + [0.0] * 1023,
        user=user,
        limit=2,
    )

    assert len(results) == 2

@pytest.mark.django_db
def test_document_processing_creates_embeddings(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="embeddingprocessinguser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Embedding Processing Test",
        original_filename="embedding.txt",
        content_type="text/plain",
    )

    document.file.save(
        "embedding.txt",
        ContentFile(
            (
                "Machine learning is useful for "
                "predictive maintenance and anomaly detection."
            ).encode("utf-8")
        ),
    )

    service = DocumentProcessingService(
        embedding_provider=FakeEmbeddingProvider(),
    )

    service.process(document)

    chunks = list(
        DocumentChunk.objects.filter(
            document=document,
        ).order_by("chunk_index")
    )

    assert len(chunks) > 0

    assert all(
        chunk.embedding is not None
        for chunk in chunks
    )

    assert all(
        len(chunk.embedding) == 1024
        for chunk in chunks
    )
import pytest

from knowledge.models import Document, DocumentChunk
from knowledge.chunking_service import DocumentChunkingService


@pytest.mark.django_db
def test_chunking_service_creates_chunks(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="chunkserviceuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Chunk Service Test",
        original_filename="notes.txt",
        content_type="text/plain",
        extracted_text=(
            "This is the first part of the document. "
            "This is the second part of the document."
        ),
    )

    service = DocumentChunkingService()

    chunks = service.create_chunks(document)

    assert len(chunks) > 0

    database_chunks = list(
        DocumentChunk.objects.filter(
            document=document,
        )
    )

    assert len(database_chunks) == len(chunks)

    assert database_chunks[0].chunk_index == 0

    assert all(
        chunk.document == document
        for chunk in database_chunks
    )

    assert all(
        chunk.content
        for chunk in database_chunks
    )


@pytest.mark.django_db
def test_chunking_service_assigns_sequential_indexes(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="indexserviceuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Index Test",
        original_filename="index.txt",
        content_type="text/plain",
        extracted_text=(
            "This is a sufficiently long document that "
            "will be divided into multiple chunks for "
            "testing sequential chunk indexes."
        ),
    )

    service = DocumentChunkingService()

    service.create_chunks(document)

    chunks = list(
        DocumentChunk.objects.filter(
            document=document,
        ).order_by("chunk_index")
    )

    assert [
        chunk.chunk_index
        for chunk in chunks
    ] == list(range(len(chunks)))


@pytest.mark.django_db
def test_chunking_service_replaces_existing_chunks(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="replacechunkuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Replace Test",
        original_filename="replace.txt",
        content_type="text/plain",
        extracted_text="New document content.",
    )

    DocumentChunk.objects.create(
        document=document,
        content="Old chunk that must disappear.",
        chunk_index=0,
    )

    service = DocumentChunkingService()

    chunks = service.create_chunks(document)

    database_chunks = list(
        DocumentChunk.objects.filter(
            document=document,
        ).order_by("chunk_index")
    )

    assert len(database_chunks) == len(chunks)

    assert all(
        "Old chunk" not in chunk.content
        for chunk in database_chunks
    )

    assert database_chunks[0].content == (
        "New document content."
    )


@pytest.mark.django_db
def test_chunking_service_creates_no_chunks_for_empty_text(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="emptychunkuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Empty Text",
        original_filename="empty.txt",
        content_type="text/plain",
        extracted_text="",
    )

    service = DocumentChunkingService()

    chunks = service.create_chunks(document)

    assert chunks == []

    assert not DocumentChunk.objects.filter(
        document=document,
    ).exists()
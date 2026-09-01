import pytest

from knowledge.models import Document, DocumentChunk


@pytest.mark.django_db
def test_document_belongs_to_user(django_user_model):
    user = django_user_model.objects.create_user(
        username="documentuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Machine Learning Notes",
        original_filename="ml_notes.pdf",
        content_type="application/pdf",
    )

    assert document.user == user
    assert document.title == "Machine Learning Notes"
    assert document.original_filename == "ml_notes.pdf"
    assert document.content_type == "application/pdf"
    assert document.status == Document.Status.PENDING


@pytest.mark.django_db
def test_document_defaults_to_pending(django_user_model):
    user = django_user_model.objects.create_user(
        username="pendinguser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Test Document",
        original_filename="test.pdf",
        content_type="application/pdf",
    )

    assert document.status == Document.Status.PENDING


@pytest.mark.django_db
def test_deleting_user_deletes_documents(django_user_model):
    user = django_user_model.objects.create_user(
        username="deleteuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="User Document",
        original_filename="document.pdf",
        content_type="application/pdf",
    )

    document_id = document.id

    user.delete()

    assert not Document.objects.filter(
        id=document_id,
    ).exists()

@pytest.mark.django_db
def test_document_chunk_belongs_to_document(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="chunkuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Chunk Test",
        original_filename="chunk.txt",
        content_type="text/plain",
    )

    chunk = DocumentChunk.objects.create(
        document=document,
        content="This is chunk content.",
        chunk_index=0,
    )

    assert chunk.document == document
    assert chunk.content == "This is chunk content."
    assert chunk.chunk_index == 0

@pytest.mark.django_db
def test_document_chunk_index_must_be_unique_per_document(
    django_user_model,
):
    from django.db import IntegrityError

    user = django_user_model.objects.create_user(
        username="uniquechunkuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Unique Chunk Test",
        original_filename="unique.txt",
        content_type="text/plain",
    )

    DocumentChunk.objects.create(
        document=document,
        content="First chunk.",
        chunk_index=0,
    )

    with pytest.raises(IntegrityError):
        DocumentChunk.objects.create(
            document=document,
            content="Duplicate chunk index.",
            chunk_index=0,
        )

@pytest.mark.django_db
def test_different_documents_can_have_same_chunk_index(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="multidocuser",
        password="test-password-123",
    )

    document_one = Document.objects.create(
        user=user,
        title="Document One",
        original_filename="one.txt",
        content_type="text/plain",
    )

    document_two = Document.objects.create(
        user=user,
        title="Document Two",
        original_filename="two.txt",
        content_type="text/plain",
    )

    chunk_one = DocumentChunk.objects.create(
        document=document_one,
        content="Document one chunk.",
        chunk_index=0,
    )

    chunk_two = DocumentChunk.objects.create(
        document=document_two,
        content="Document two chunk.",
        chunk_index=0,
    )

    assert chunk_one.chunk_index == 0
    assert chunk_two.chunk_index == 0

@pytest.mark.django_db
def test_deleting_document_deletes_chunks(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="cascadechunkuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Cascade Test",
        original_filename="cascade.txt",
        content_type="text/plain",
    )

    chunk = DocumentChunk.objects.create(
        document=document,
        content="Chunk to delete.",
        chunk_index=0,
    )

    chunk_id = chunk.id

    document.delete()

    assert not DocumentChunk.objects.filter(
        id=chunk_id,
    ).exists()


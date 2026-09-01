import pytest

from knowledge.models import Document, DocumentChunk


@pytest.mark.django_db
def test_document_chunk_can_store_and_retrieve_embedding(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="vectorstorageuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Vector Storage Test",
        original_filename="vector.txt",
        content_type="text/plain",
    )

    embedding = [0.1] * 1024

    chunk = DocumentChunk.objects.create(
        document=document,
        content="Machine learning is useful.",
        chunk_index=0,
        embedding=embedding,
    )

    chunk.refresh_from_db()

    assert chunk.embedding is not None
    assert len(chunk.embedding) == 1024

    assert chunk.embedding[0] == pytest.approx(0.1)
    assert chunk.embedding[-1] == pytest.approx(0.1)
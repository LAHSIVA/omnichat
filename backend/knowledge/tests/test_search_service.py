import pytest

from knowledge.models import Document, DocumentChunk
from knowledge.search_service import DocumentSearchService


@pytest.mark.django_db
def test_search_returns_most_similar_chunks(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="searchuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Search Test",
        original_filename="search.txt",
        content_type="text/plain",
    )

    DocumentChunk.objects.create(
        document=document,
        content="Machine learning and artificial intelligence.",
        chunk_index=0,
        embedding=[1.0] + [0.0] * 1023,
    )

    DocumentChunk.objects.create(
        document=document,
        content="Cooking recipes and kitchen equipment.",
        chunk_index=1,
        embedding=[0.0, 1.0] + [0.0] * 1022,
    )

    service = DocumentSearchService()

    results = service.search(
        query_embedding=[1.0] + [0.0] * 1023,
        user=user,
        limit=1,
    )

    assert len(results) == 1

    assert results[0].content == (
        "Machine learning and artificial intelligence."
    )
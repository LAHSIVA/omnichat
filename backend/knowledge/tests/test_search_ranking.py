import pytest

from knowledge.models import Document, DocumentChunk
from knowledge.search_service import DocumentSearchService


@pytest.mark.django_db
def test_search_orders_chunks_by_similarity(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="rankinguser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Ranking Test",
        original_filename="ranking.txt",
        content_type="text/plain",
    )

    query_embedding = [1.0] + [0.0] * 1023

    DocumentChunk.objects.create(
        document=document,
        content="Highly relevant content.",
        chunk_index=0,
        embedding=[0.99] + [0.0] * 1023,
    )

    DocumentChunk.objects.create(
        document=document,
        content="Somewhat relevant content.",
        chunk_index=1,
        embedding=[0.5] + [0.8660254] + [0.0] * 1022,
    )

    DocumentChunk.objects.create(
        document=document,
        content="Unrelated content.",
        chunk_index=2,
        embedding=[0.0, 1.0] + [0.0] * 1022,
    )

    service = DocumentSearchService()

    results = service.search(
        query_embedding=query_embedding,
        user=user,
        limit=3,
    )

    assert len(results) == 2

    assert results[0].content == (
        "Highly relevant content."
    )

    assert results[1].content == (
        "Somewhat relevant content."
    )


@pytest.mark.django_db
def test_search_excludes_chunks_above_similarity_threshold(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="thresholduser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Threshold Test",
        original_filename="threshold.txt",
        content_type="text/plain",
    )

    query_embedding = [1.0] + [0.0] * 1023

    DocumentChunk.objects.create(
        document=document,
        content="Relevant content.",
        chunk_index=0,
        embedding=[0.9] + [0.4358899] + [0.0] * 1022,
    )

    DocumentChunk.objects.create(
        document=document,
        content="Irrelevant content.",
        chunk_index=1,
        embedding=[0.3] + [0.9539392] + [0.0] * 1022,
    )

    service = DocumentSearchService(
        max_distance=0.50,
    )

    results = service.search(
        query_embedding=query_embedding,
        user=user,
        limit=5,
    )

    assert len(results) == 1
    assert results[0].content == "Relevant content."
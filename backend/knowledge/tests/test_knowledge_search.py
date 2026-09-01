import pytest

from knowledge.embeddings import FakeEmbeddingProvider
from knowledge.models import Document, DocumentChunk
from knowledge.knowledge_search import KnowledgeSearchService


@pytest.mark.django_db
def test_knowledge_search_embeds_query_and_returns_chunks(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="knowledgesearchuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Knowledge Search Test",
        original_filename="knowledge.txt",
        content_type="text/plain",
    )

    DocumentChunk.objects.create(
        document=document,
        content="Hello",
        chunk_index=0,
        embedding=[5.0] + [0.0] * 1023,
    )

    embedding_provider = FakeEmbeddingProvider()

    service = KnowledgeSearchService(
        embedding_provider=embedding_provider,
    )

    results = service.search(
        query="Hello",
        user=user,
        limit=1,
    )

    assert len(results) == 1

    assert results[0].content == "Hello"
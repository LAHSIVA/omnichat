import pytest

from django.contrib.auth import get_user_model

from knowledge.embeddings import OllamaEmbeddingProvider
from knowledge.knowledge_search import KnowledgeSearchService
from knowledge.models import Document, DocumentChunk


@pytest.mark.integration
@pytest.mark.django_db
def test_knowledge_search_uses_bge_m3_for_query_embedding(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="realsearchuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Predictive Maintenance",
        original_filename="maintenance.txt",
        content_type="text/plain",
    )

    embedding_provider = OllamaEmbeddingProvider()

    relevant_text = (
        "Predictive maintenance uses machine learning "
        "to detect equipment failures before they happen."
    )

    irrelevant_text = (
        "The company cafeteria serves lunch from twelve "
        "o'clock every afternoon."
    )

    relevant_embedding = embedding_provider.embed(
        [relevant_text]
    )[0]

    irrelevant_embedding = embedding_provider.embed(
        [irrelevant_text]
    )[0]

    DocumentChunk.objects.create(
        document=document,
        content=relevant_text,
        chunk_index=0,
        embedding=relevant_embedding,
    )

    DocumentChunk.objects.create(
        document=document,
        content=irrelevant_text,
        chunk_index=1,
        embedding=irrelevant_embedding,
    )

    service = KnowledgeSearchService(
        embedding_provider=embedding_provider,
    )

    results = service.search(
        query="How can machine learning predict equipment failures?",
        user=user,
        limit=2,
    )

    assert len(results) == 1
    assert results[0].content == relevant_text
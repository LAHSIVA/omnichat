import pytest

from knowledge.embeddings import OllamaEmbeddingProvider
from knowledge.knowledge_search import KnowledgeSearchService
from knowledge.models import Document, DocumentChunk


@pytest.mark.integration
@pytest.mark.django_db
def test_bge_m3_semantically_ranks_relevant_chunks(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="bgerankinguser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="BGE Ranking Test",
        original_filename="ranking.txt",
        content_type="text/plain",
    )

    contents = [
        "Python is widely used for machine learning and artificial intelligence.",
        "The weather in Chennai is hot during summer.",
        "PostgreSQL is a relational database management system.",
    ]

    embedding_provider = OllamaEmbeddingProvider()

    embeddings = embedding_provider.embed(contents)

    DocumentChunk.objects.bulk_create(
        [
            DocumentChunk(
                document=document,
                content=content,
                chunk_index=index,
                embedding=embedding,
            )
            for index, (content, embedding)
            in enumerate(zip(contents, embeddings))
        ]
    )

    search_service = KnowledgeSearchService(
        embedding_provider=embedding_provider,
    )

    results = search_service.search(
        query="Which programming language is commonly used for machine learning?",
        user=user,
        limit=3,
    )

    assert len(results) == 1

    assert results[0].content == (
        "Python is widely used for machine learning and artificial intelligence."
    )
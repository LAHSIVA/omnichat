import pytest

from knowledge.embeddings import OllamaEmbeddingProvider
from knowledge.models import Document, DocumentChunk
from knowledge.search_service import DocumentSearchService


@pytest.mark.integration
@pytest.mark.django_db
def test_measure_bge_m3_search_distances(django_user_model):
    user = django_user_model.objects.create_user(
        username="distanceuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Distance Test",
        original_filename="distance.txt",
        content_type="text/plain",
    )

    contents = [
        "Python is widely used for machine learning and artificial intelligence.",
        "Machine learning models can be trained using Python and scikit-learn.",
        "PostgreSQL is a relational database management system.",
        "The weather in Chennai is hot during summer.",
        "Bananas are a good source of potassium.",
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

    query = "Which programming language is commonly used for machine learning?"

    query_embedding = embedding_provider.embed([query])[0]

    service = DocumentSearchService()

    results = service.search(
        query_embedding=query_embedding,
        user=user,
        limit=5,
    )

    for result in results:
        print(
            f"\nDistance: {result.distance:.6f}"
            f"\nContent: {result.content}"
        )

    assert len(results) == 2
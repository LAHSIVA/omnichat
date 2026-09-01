import pytest

from knowledge.embeddings import OllamaEmbeddingProvider
from knowledge.knowledge_search import KnowledgeSearchService
from knowledge.models import Document, DocumentChunk


@pytest.mark.integration
@pytest.mark.django_db
def test_knowledge_search_returns_no_results_when_nothing_is_relevant(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="norelevantuser",
        password="test-password-123",
    )

    document = Document.objects.create(
        user=user,
        title="Machine Learning Notes",
        original_filename="ml.txt",
        content_type="text/plain",
    )

    embedding_provider = OllamaEmbeddingProvider()

    document_text = (
        "Machine learning models can be trained using "
        "Python and scikit-learn."
    )

    document_embedding = embedding_provider.embed(
        [document_text]
    )[0]

    DocumentChunk.objects.create(
        document=document,
        content=document_text,
        chunk_index=0,
        embedding=document_embedding,
    )

    service = KnowledgeSearchService(
        embedding_provider=embedding_provider,
    )

    results = service.search(
        query="What is the company's employee leave policy?",
        user=user,
        limit=5,
    )

    assert results == []
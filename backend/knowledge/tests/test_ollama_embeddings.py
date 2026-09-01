import pytest

from knowledge.embeddings import OllamaEmbeddingProvider


@pytest.mark.integration
def test_ollama_bge_m3_returns_1024_dimensional_embedding():
    provider = OllamaEmbeddingProvider()

    embeddings = provider.embed(
        ["Machine learning is useful."]
    )

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1024
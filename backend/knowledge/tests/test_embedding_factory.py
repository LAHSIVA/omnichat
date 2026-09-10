import pytest

from knowledge.embedding_factory import create_embedding_provider
from knowledge.embeddings import (
    FakeEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
    OllamaEmbeddingProvider,
)


@pytest.mark.parametrize(
    ("provider_name", "provider_type"),
    [
        ("ollama", OllamaEmbeddingProvider),
        ("huggingface", HuggingFaceEmbeddingProvider),
        ("fake", FakeEmbeddingProvider),
    ],
)
def test_create_embedding_provider(
    settings,
    provider_name,
    provider_type,
):
    settings.EMBEDDING_PROVIDER = provider_name

    provider = create_embedding_provider()

    assert isinstance(provider, provider_type)


def test_create_embedding_provider_rejects_unknown_provider(settings):
    settings.EMBEDDING_PROVIDER = "unknown"

    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        create_embedding_provider()

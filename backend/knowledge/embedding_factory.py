from django.conf import settings

from knowledge.embeddings import (
    EmbeddingProvider,
    FakeEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
    OllamaEmbeddingProvider,
)


def create_embedding_provider() -> EmbeddingProvider:
    """Create the configured embedding provider."""
    provider = settings.EMBEDDING_PROVIDER

    if provider == "ollama":
        return OllamaEmbeddingProvider()

    if provider == "huggingface":
        return HuggingFaceEmbeddingProvider()

    if provider == "fake":
        return FakeEmbeddingProvider()

    raise ValueError(
        f"Unsupported embedding provider: {provider}"
    )

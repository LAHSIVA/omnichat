from knowledge.embeddings import (
    EmbeddingProvider,
    FakeEmbeddingProvider,
)


def test_embedding_provider_defines_embed_contract():
    provider = EmbeddingProvider()

    try:
        provider.embed(["hello"])
    except NotImplementedError:
        pass
    else:
        raise AssertionError(
            "Base embedding provider must define an abstract contract."
        )


def test_fake_embedding_provider_returns_one_vector_per_text():
    provider = FakeEmbeddingProvider()

    texts = [
        "hello",
        "machine learning",
        "RAG",
    ]

    vectors = provider.embed(texts)

    assert len(vectors) == len(texts)

    assert all(
        isinstance(vector, list)
        for vector in vectors
    )

    assert all(
    len(vector) == 1024
    for vector in vectors
    )   


def test_fake_embedding_provider_is_deterministic():
    provider = FakeEmbeddingProvider()

    texts = [
        "hello",
        "machine learning",
    ]

    first = provider.embed(texts)
    second = provider.embed(texts)

    assert first == second
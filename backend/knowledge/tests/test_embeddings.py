from unittest.mock import Mock

from knowledge.embeddings import (
    EmbeddingProvider,
    FakeEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
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

def test_huggingface_embedding_provider_returns_embeddings(monkeypatch):
    fake_client = Mock()
    fake_client.feature_extraction.return_value = Mock(
        tolist=lambda: [
            [0.1] * 1024,
            [0.2] * 1024,
        ]
    )

    monkeypatch.setattr(
        "huggingface_hub.InferenceClient",
        lambda **kwargs: fake_client,
    )

    provider = HuggingFaceEmbeddingProvider(
        api_key="test-token",
    )

    embeddings = provider.embed(
        ["hello", "world"],
    )

    fake_client.feature_extraction.assert_called_once_with(
        text=["hello", "world"],
        model="Qwen/Qwen3-Embedding-0.6B",
    )

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1024
    assert len(embeddings[1]) == 1024



def test_huggingface_embedding_provider_requires_token():
    provider = HuggingFaceEmbeddingProvider(
        api_key="",
    )

    try:
        provider.embed(["hello"])
    except ValueError as exc:
        assert "HF_TOKEN" in str(exc)
    else:
        raise AssertionError(
            "Expected missing token to raise ValueError"
        )


def test_huggingface_embedding_provider_validates_dimensions(
    monkeypatch,
):
    fake_client = Mock()
    fake_client.feature_extraction.return_value = Mock(
        tolist=lambda: [[0.1] * 10]
    )

    monkeypatch.setattr(
        "huggingface_hub.InferenceClient",
        lambda **kwargs: fake_client,
    )

    provider = HuggingFaceEmbeddingProvider(
        api_key="test-token",
    )

    try:
        provider.embed(["hello"])
    except ValueError as exc:
        assert "dimension 10" in str(exc)
        assert "expected 1024" in str(exc)
    else:
        raise AssertionError(
            "Expected dimension validation to fail"
        )

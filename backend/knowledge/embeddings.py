import logging
from time import perf_counter

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Base interface for embedding providers."""

    def embed(self, texts):
        raise NotImplementedError


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic embedding provider for tests."""

    DIMENSIONS = 1024

    def embed(self, texts):
        return [
            [float(len(text))] + [0.0] * (self.DIMENSIONS - 1)
            for text in texts
        ]


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Generate embeddings using an Ollama embedding model."""

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "Qwen/Qwen3-Embedding-0.6B"
    DEFAULT_DIMENSIONS = 1024

    def __init__(
        self,
        base_url=None,
        model=None,
        dimensions=None,
        timeout=60,
    ):
        self.base_url = (
            base_url
            or getattr(
                settings,
                "OLLAMA_BASE_URL",
                self.DEFAULT_BASE_URL,
            )
        ).rstrip("/")

        self.model = (
            model
            or getattr(
                settings,
                "OLLAMA_EMBEDDING_MODEL",
                self.DEFAULT_MODEL,
            )
        )

        self.dimensions = int(
            dimensions
            or getattr(
                settings,
                "OLLAMA_EMBEDDING_DIMENSIONS",
                self.DEFAULT_DIMENSIONS,
            )
        )

        self.timeout = timeout

    def embed(self, texts):
        """Generate embeddings for the supplied texts."""
        if not texts:
            return []

        start_time = perf_counter()

        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": texts,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()
            embeddings = data["embeddings"]

            if len(embeddings) != len(texts):
                raise ValueError(
                    "Embedding provider returned an unexpected "
                    "number of embeddings."
                )

            for embedding in embeddings:
                if len(embedding) != self.dimensions:
                    raise ValueError(
                        f"Expected {self.dimensions}-dimensional "
                        f"embedding, got {len(embedding)}."
                    )

            duration_ms = (
                perf_counter() - start_time
            ) * 1000

            logger.info(
                "Embedding request completed",
                extra={
                    "provider": "ollama",
                    "model": self.model,
                    "text_count": len(texts),
                    "duration_ms": round(
                        duration_ms,
                        2,
                    ),
                },
            )

            return embeddings

        except Exception as exc:
            duration_ms = (
                perf_counter() - start_time
            ) * 1000

            logger.error(
                "Embedding request failed",
                extra={
                    "provider": "ollama",
                    "model": self.model,
                    "text_count": len(texts),
                    "duration_ms": round(
                        duration_ms,
                        2,
                    ),
                    "error_type": type(exc).__name__,
                },
            )

            raise



class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Generate embeddings using Hugging Face Inference Providers."""

    DEFAULT_MODEL = "Qwen/Qwen3-Embedding-0.6B"
    DEFAULT_DIMENSIONS = 1024

    def __init__(
        self,
        api_key=None,
        model=None,
        dimensions=None,
        timeout=60,
    ):
        self.api_key = (
        getattr(settings, "HF_TOKEN", "")
        if api_key is None
        else api_key
    )
        self.model = model or getattr(
            settings,
            "HF_EMBEDDING_MODEL",
            self.DEFAULT_MODEL,
        )
        self.dimensions = int(
            dimensions
            or getattr(
                settings,
                "HF_EMBEDDING_DIMENSIONS",
                self.DEFAULT_DIMENSIONS,
            )
        )
        self.timeout = timeout

    def embed(self, texts):
        """Generate embeddings for the supplied texts."""
        if not texts:
            return []

        if not self.api_key:
            raise ValueError(
                "HF_TOKEN is required for Hugging Face embeddings."
            )

        from huggingface_hub import InferenceClient

        start_time = perf_counter()

        try:
            client = InferenceClient(
                api_key=self.api_key,
                timeout=self.timeout,
            )

            result = client.feature_extraction(
                text=texts,
                model=self.model,
            )

            embeddings = result.tolist()

            if len(embeddings) != len(texts):
                raise ValueError(
                    "Hugging Face returned an unexpected number "
                    "of embeddings."
                )

            for embedding in embeddings:
                if len(embedding) != self.dimensions:
                    raise ValueError(
                        "Hugging Face returned an embedding with "
                        f"dimension {len(embedding)}, expected "
                        f"{self.dimensions}."
                    )

            duration_ms = (perf_counter() - start_time) * 1000

            logger.info(
                "Generated embeddings",
                extra={
                    "provider": "huggingface",
                    "model": self.model,
                    "text_count": len(texts),
                    "duration_ms": round(duration_ms, 2),
                },
            )

            return embeddings

        except Exception as exc:
            logger.error(
                "Embedding request failed",
                extra={
                    "provider": "huggingface",
                    "model": self.model,
                    "text_count": len(texts),
                },
                exc_info=True,
            )
            raise

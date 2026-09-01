from django.conf import settings
import requests


class EmbeddingProvider:
    def embed(self, texts):
        raise NotImplementedError


class FakeEmbeddingProvider(EmbeddingProvider):
    DIMENSIONS = 1024

    def embed(self, texts):
        return [
            [float(len(text))] + [0.0] * (self.DIMENSIONS - 1)
            for text in texts
        ]


class OllamaEmbeddingProvider(EmbeddingProvider):
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "bge-m3"
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
        if not texts:
            return []

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

        return embeddings
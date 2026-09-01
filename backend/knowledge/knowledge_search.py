from knowledge.embeddings import (
    EmbeddingProvider,
    OllamaEmbeddingProvider,
)
from knowledge.search_service import DocumentSearchService


class KnowledgeSearchService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        search_service: DocumentSearchService | None = None,
    ):
        self.embedding_provider = (
            embedding_provider
            or OllamaEmbeddingProvider()
        )

        self.search_service = (
            search_service
            or DocumentSearchService()
        )

    def search(
        self,
        query: str,
        user,
        limit: int = 5,
    ):
        query_embedding = self.embedding_provider.embed(
            [query],
        )[0]

        return self.search_service.search(
            query_embedding=query_embedding,
            user=user,
            limit=limit,
        )
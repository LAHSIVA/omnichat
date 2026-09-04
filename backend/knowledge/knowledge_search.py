from ai.domain.types import RetrievedChunk

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

        chunks = self.search_service.search(
            query_embedding=query_embedding,
            user=user,
            limit=limit,
        )

        return [
            RetrievedChunk(
                content=chunk.content,
                document_id=chunk.document_id,
                document_title=chunk.document.title,
                original_filename=chunk.document.original_filename,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                distance=(
                    float(chunk.distance)
                    if chunk.distance is not None
                    else None
                ),
            )
            for chunk in chunks
        ]
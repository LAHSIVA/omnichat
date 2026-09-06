import logging
from time import perf_counter

from django.conf import settings
from pgvector.django import CosineDistance

from knowledge.models import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentSearchService:
    """Search document chunks using pgvector cosine similarity."""

    DEFAULT_MAX_DISTANCE = 0.50

    def __init__(self, max_distance=None):
        self.max_distance = (
            max_distance
            if max_distance is not None
            else getattr(
                settings,
                "KNOWLEDGE_SEARCH_MAX_DISTANCE",
                self.DEFAULT_MAX_DISTANCE,
            )
        )

    def search(
        self,
        query_embedding,
        user,
        limit=5,
    ):
        start_time = perf_counter()

        try:
            chunks = list(
                DocumentChunk.objects.filter(
                    document__user=user,
                    embedding__isnull=False,
                )
                .annotate(
                    distance=CosineDistance(
                        "embedding",
                        query_embedding,
                    )
                )
                .filter(
                    distance__lte=self.max_distance,
                )
                .order_by("distance")[:limit]
            )

            duration_ms = (perf_counter() - start_time) * 1000

            logger.info(
                "Vector search completed",
                extra={
                    "service": "document_search",
                    "result_count": len(chunks),
                    "limit": limit,
                    "max_distance": self.max_distance,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            if chunks:
                logger.info(
                    "Vector search best match",
                    extra={
                        "service": "document_search",
                        "best_distance": round(
                            float(chunks[0].distance),
                            4,
                        ),
                    },
                )

            return chunks

        except Exception as exc:
            duration_ms = (perf_counter() - start_time) * 1000

            logger.error(
                "Vector search failed",
                extra={
                    "service": "document_search",
                    "duration_ms": round(duration_ms, 2),
                    "error_type": type(exc).__name__,
                },
            )
            raise

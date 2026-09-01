from django.conf import settings
from pgvector.django import CosineDistance

from knowledge.models import DocumentChunk


class DocumentSearchService:
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
        return list(
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
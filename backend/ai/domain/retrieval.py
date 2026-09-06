from dataclasses import dataclass

from ai.domain.types import RetrievedChunk


@dataclass(frozen=True)
class RetrievalResult:
    """Represents retrieved document context and its relevance."""

    chunks: list[RetrievedChunk]
    is_relevant: bool

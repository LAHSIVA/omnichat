from enum import StrEnum


class ResponseMode(StrEnum):
    """Defines how OmniChat should answer a user query."""

    GENERAL = "general"
    RAG = "rag"

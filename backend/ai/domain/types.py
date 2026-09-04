from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    is_optional: bool = False


@dataclass(frozen=True)
class RetrievedChunk:
    content: str
    document_id: int
    document_title: str
    original_filename: str
    chunk_id: int
    chunk_index: int
    distance: float | None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: TokenUsage | None
    finish_reason: str | None
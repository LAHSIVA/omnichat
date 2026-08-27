from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


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
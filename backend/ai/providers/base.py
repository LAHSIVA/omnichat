from abc import ABC, abstractmethod
from collections.abc import Iterator

from ai.domain.types import ChatMessage, LLMResponse


class LLMProvider(ABC):
    """Contract implemented by every LLM provider."""

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a non-streaming response."""
        raise NotImplementedError

    @abstractmethod
    def generate_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """Generate a response incrementally."""
        raise NotImplementedError
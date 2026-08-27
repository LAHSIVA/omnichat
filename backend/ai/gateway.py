from ai.domain.types import ChatMessage, LLMResponse
from ai.providers.base import LLMProvider


class LLMGateway:
    """Routes LLM requests to the configured provider."""

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
    ) -> None:
        self.provider = provider
        self.model = model

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        return self.provider.generate(
            messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
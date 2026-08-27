from ai.domain.types import ChatMessage, LLMResponse, TokenUsage
from ai.providers.base import LLMProvider


class FakeLLMProvider(LLMProvider):
    """Deterministic provider used for testing."""

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            content="This is a fake AI response.",
            model=model,
            provider="fake",
            usage=TokenUsage(
                input_tokens=10,
                output_tokens=6,
            ),
            finish_reason="stop",
        )
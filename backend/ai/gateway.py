from ai.domain.types import ChatMessage, LLMResponse
from ai.providers.base import LLMProvider
from ai.resilience.retry import RetryPolicy


class LLMGateway:
    """Routes LLM requests to the configured provider."""

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.retry_policy = retry_policy or RetryPolicy()

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        return self.retry_policy.execute(
            lambda: self.provider.generate(
                messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
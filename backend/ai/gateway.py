from ai.domain.types import ChatMessage, LLMResponse
from ai.providers.base import LLMProvider
from ai.resilience.retry import RetryPolicy
import logging
from time import perf_counter
logger = logging.getLogger(__name__)
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
        logger.info(
            "LLM request started",
            extra={
                "provider": self.provider.__class__.__name__,
                "model": self.model,
            },
        )

        start_time = perf_counter()

        try:
            response = self.retry_policy.execute(
                lambda: self.provider.generate(
                    messages,
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )

        except Exception as exc:
            duration_ms = (perf_counter() - start_time) * 1000

            logger.error(
                "LLM request failed",
                extra={
                    "provider": self.provider.__class__.__name__,
                    "model": self.model,
                    "error_type": type(exc).__name__,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            raise

        duration_ms = (perf_counter() - start_time) * 1000

        usage = response.usage

        logger.info(
            "LLM request completed",
            extra={
                "provider": response.provider,
                "model": response.model,
                "duration_ms": round(duration_ms, 2),
                "input_tokens": (
                    usage.input_tokens
                    if usage is not None
                    else None
                ),
                "output_tokens": (
                    usage.output_tokens
                    if usage is not None
                    else None
                ),
            },
        )

        return response
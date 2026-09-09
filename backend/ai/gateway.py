import logging
from time import perf_counter

from ai.domain.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from ai.domain.types import ChatMessage, LLMResponse
from ai.providers.base import LLMProvider
from ai.resilience.model_fallback import ModelFallbackPolicy
from ai.resilience.retry import RetryPolicy

logger = logging.getLogger(__name__)


class LLMGateway:
    """Gateway that adds retry and observability around an LLM provider."""

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        retry_policy: RetryPolicy | None = None,
        *,
        enable_fallback: bool = False,
    ) -> None:
        self.provider = provider
        self.model = model
        self.retry_policy = retry_policy or RetryPolicy()
        self.enable_fallback = enable_fallback

    def _model_candidates(self) -> tuple[str, ...]:
        """Return models in fallback priority order."""
        return tuple(ModelFallbackPolicy.candidates(self.model))

    def _generate_candidate(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Generate a response using one model with retry handling."""
        attempts = 0
        provider_name = type(self.provider).__name__

        def operation() -> LLMResponse:
            nonlocal attempts
            attempts += 1

            if attempts > 1:
                logger.info(
                    "LLM request retrying",
                    extra={
                        "provider": provider_name,
                        "model": model,
                        "attempt": attempts,
                        "next_attempt": attempts + 1,
                        "max_attempts": self.retry_policy.max_attempts,
                    },
                )

            return self.provider.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return self.retry_policy.execute(operation)


    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate a response with retry and optional model fallback."""
        start_time = perf_counter()

        provider_name = type(self.provider).__name__
        candidates = (
            self._model_candidates()
            if self.enable_fallback
            else (self.model,)
        )

        logger.info(
            "LLM request started",
            extra={
                "provider": provider_name,
                "model": self.model,
            },
        )

        last_error: Exception | None = None

        for candidate_index, candidate_model in enumerate(candidates):
            try:
                response = self._generate_candidate(
                    messages=messages,
                    model=candidate_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                duration_ms = (perf_counter() - start_time) * 1000

                input_tokens = None
                output_tokens = None

                if response.usage is not None:
                    input_tokens = response.usage.input_tokens
                    output_tokens = response.usage.output_tokens

                logger.info(
                    "LLM request completed",
                    extra={
                        "provider": response.provider,
                        "model": response.model,
                        "duration_ms": round(duration_ms, 2),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                )

                return response

            except (LLMRateLimitError, LLMTimeoutError, LLMProviderError) as exc:
                last_error = exc

                if candidate_index >= len(candidates) - 1:
                    break

                logger.warning(
                    "LLM model fallback",
                    extra={
                        "provider": provider_name,
                        "failed_model": candidate_model,
                        "fallback_model": candidates[candidate_index + 1],
                        "error_type": type(exc).__name__,
                    },
                )

        duration_ms = (perf_counter() - start_time) * 1000

        logger.error(
            "LLM request failed",
            extra={
                "provider": provider_name,
                "model": self.model,
                "duration_ms": round(duration_ms, 2),
                "error_type": type(last_error).__name__,
            },
        )

        if last_error is not None:
            raise last_error

        raise RuntimeError("LLM request failed without an exception.")
    # Streaming retries and telemetry intentionally keep this state together.
    def generate_stream(  # pylint: disable=too-many-locals
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ):
        overall_start = perf_counter()

        provider_name = type(self.provider).__name__

        candidates = (
            self._model_candidates()
            if self.enable_fallback
            else (self.model,)
        )

        logger.info(
            "LLM streaming request started",
            extra={
                "provider": provider_name,
                "model": self.model,
            },
        )

        for candidate_index, candidate_model in enumerate(candidates):
            max_attempts = self.retry_policy.max_attempts

            for attempt in range(1, max_attempts + 1):
                attempt_start = perf_counter()
                chunks_received = False

                logger.info(
                    "LLM streaming attempt started",
                    extra={
                        "provider": provider_name,
                        "model": candidate_model,
                        "attempt": attempt,
                    },
                )

                try:
                    stream = self.provider.generate_stream(
                        messages=messages,
                        model=candidate_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                    for chunk in stream:
                        if not chunks_received:
                            chunks_received = True

                            ttft_ms = (
                                perf_counter() - attempt_start
                            ) * 1000

                            logger.info(
                                "LLM first token received",
                                extra={
                                    "provider": provider_name,
                                    "model": candidate_model,
                                    "attempt": attempt,
                                    "duration_ms": round(
                                        ttft_ms,
                                        2,
                                    ),
                                    "ttft_ms": round(
                                        ttft_ms,
                                        2,
                                    ),
                                },
                            )

                        yield chunk

                    attempt_duration_ms = (
                        perf_counter() - attempt_start
                    ) * 1000

                    overall_duration_ms = (
                        perf_counter() - overall_start
                    ) * 1000

                    logger.info(
                        "LLM streaming request completed",
                        extra={
                            "provider": provider_name,
                            "model": candidate_model,
                            "attempt": attempt,
                            "duration_ms": round(
                                attempt_duration_ms,
                                2,
                            ),
                            "overall_duration_ms": round(
                                overall_duration_ms,
                                2,
                            ),
                            "chunks_received": chunks_received,
                        },
                    )

                    return

                except LLMRateLimitError as exc:
                    logger.warning(
                        "LLM streaming attempt rate limited",
                        extra={
                            "provider": provider_name,
                            "model": candidate_model,
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                        },
                    )

                    if chunks_received:
                        raise

                    if candidate_index < len(candidates) - 1:
                        break

                    raise exc

                except (LLMTimeoutError, LLMProviderError) as exc:
                    logger.error(
                        "LLM streaming attempt failed",
                        extra={
                            "provider": provider_name,
                            "model": candidate_model,
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "error_type": type(exc).__name__,
                        },
                        exc_info=True,
                    )

                    if chunks_received:
                        raise

                    if attempt < max_attempts:
                        logger.info(
                            "Retrying LLM streaming request",
                            extra={
                                "provider": provider_name,
                                "model": candidate_model,
                                "attempt": attempt,
                                "next_attempt": attempt + 1,
                            },
                        )

                        self.retry_policy.sleep()
                        continue

                    if candidate_index < len(candidates) - 1:
                        logger.warning(
                            "LLM streaming model fallback",
                            extra={
                                "provider": provider_name,
                                "failed_model": candidate_model,
                                "fallback_model": (
                                    candidates[candidate_index + 1]
                                ),
                                "error_type": type(exc).__name__,
                            },
                        )
                        break

                    raise

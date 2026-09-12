import logging
from collections.abc import Iterator
from time import perf_counter

from ai.domain.exceptions import (
    LLMAuthenticationError,
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
    """
    Central gateway for LLM calls.

    The gateway supports two fallback mechanisms:

    1. Model fallback:
       Try alternate models using the same provider.

    2. Provider fallback:
       If the primary provider fails, switch to a secondary provider.

    Provider fallback is preferred when configured.
    """

    FALLBACK_ERRORS = (
        LLMRateLimitError,
        LLMTimeoutError,
        LLMProviderError,
    )

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        retry_policy: RetryPolicy | None = None,
        *,
        fallback_provider: LLMProvider | None = None,
        fallback_model: str = "auto",
        enable_fallback: bool = False,
    ) -> None:
        self.provider = provider
        self.fallback_provider = fallback_provider
        self.model = model
        self.fallback_model = fallback_model
        self.retry_policy = retry_policy or RetryPolicy()
        self.enable_fallback = enable_fallback

    @staticmethod
    def _provider_name(provider: LLMProvider) -> str:
        return type(provider).__name__

    def _provider_candidates(
        self,
    ) -> list[tuple[LLMProvider, str]]:
        """
        Build the ordered provider/model fallback chain.

        If a secondary provider exists:

            primary provider + primary model
            secondary provider + fallback model

        Otherwise use the model fallback policy on the
        primary provider.
        """

        if not self.enable_fallback:
            return [(self.provider, self.model)]

        if self.fallback_provider is not None:
            return [
                (self.provider, self.model),
                (self.fallback_provider, self.fallback_model),
            ]

        models = ModelFallbackPolicy.candidates(self.model)

        return [
            (self.provider, candidate_model)
            for candidate_model in models
        ]

    def _generate_with_provider(
        self,
        provider: LLMProvider,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        attempts = 0

        def operation() -> LLMResponse:
            nonlocal attempts
            attempts += 1

            logger.info(
                "LLM provider attempt",
                extra={
                    "provider": self._provider_name(provider),
                    "model": model,
                    "attempt": attempts,
                },
            )

            return provider.generate(
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
        """Generate a response with automatic fallback."""

        start_time = perf_counter()
        last_error: Exception | None = None

        candidates = self._provider_candidates()

        for index, (provider, model) in enumerate(candidates):
            provider_name = self._provider_name(provider)

            logger.info(
                "LLM request started",
                extra={
                    "provider": provider_name,
                    "model": model,
                    "provider_index": index,
                },
            )

            try:
                response = self._generate_with_provider(
                    provider,
                    messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                duration_ms = (
                    perf_counter() - start_time
                ) * 1000

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
                        "finish_reason": response.finish_reason,
                    },
                )

                return response

            except self.FALLBACK_ERRORS as exc:
                last_error = exc

                logger.warning(
                    "LLM provider failed",
                    extra={
                        "provider": provider_name,
                        "model": model,
                        "error_type": type(exc).__name__,
                    },
                )

                if index < len(candidates) - 1:
                    next_provider, next_model = candidates[index + 1]

                    logger.warning(
                        "Switching LLM fallback",
                        extra={
                            "failed_provider": provider_name,
                            "failed_model": model,
                            "fallback_provider": self._provider_name(
                                next_provider
                            ),
                            "fallback_model": next_model,
                        },
                    )

        duration_ms = (
            perf_counter() - start_time
        ) * 1000

        logger.error(
            "LLM request failed",
            extra={
                "provider": self._provider_name(
                    candidates[-1][0]
                ),
                "model": candidates[-1][1],
                "error_type": (
                    type(last_error).__name__
                    if last_error is not None
                    else None
                ),
                "duration_ms": round(duration_ms, 2),
            },
        )

        if last_error is not None:
            raise last_error

        raise LLMProviderError(
            "No LLM provider was available."
        )

    def generate_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> Iterator[str]:
        """
        Stream from the first available provider/model.

        Fallback is allowed only before the first token is emitted.
        Once output has reached the client, switching providers would
        corrupt or duplicate the response.
        """

        start_time = perf_counter()
        candidates = self._provider_candidates()

        for index, (provider, model) in enumerate(candidates):
            provider_name = self._provider_name(provider)
            chunks_received = False

            logger.info(
                "LLM streaming provider started",
                extra={
                    "provider": provider_name,
                    "model": model,
                    "provider_index": index,
                },
            )

            try:
                stream = provider.generate_stream(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                for chunk in stream:
                    chunks_received = True
                    yield chunk

                duration_ms = (
                    perf_counter() - start_time
                ) * 1000

                logger.info(
                    "LLM streaming request completed",
                    extra={
                        "provider": provider_name,
                        "model": model,
                        "duration_ms": round(duration_ms, 2),
                    },
                )

                return

            except self.FALLBACK_ERRORS as exc:
                logger.warning(
                    "LLM streaming provider failed",
                    extra={
                        "provider": provider_name,
                        "model": model,
                        "error_type": type(exc).__name__,
                        "chunks_received": chunks_received,
                    },
                )

                # Never switch providers after partial output.
                if chunks_received:
                    raise

                if index >= len(candidates) - 1:
                    raise

                next_provider, next_model = candidates[index + 1]

                logger.warning(
                    "Switching streaming request to fallback",
                    extra={
                        "failed_provider": provider_name,
                        "failed_model": model,
                        "fallback_provider": self._provider_name(
                            next_provider
                        ),
                        "fallback_model": next_model,
                    },
                )

                continue

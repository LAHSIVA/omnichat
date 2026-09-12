import logging
from collections.abc import Iterator
from time import perf_counter

from django.conf import settings
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from ai.domain.types import (
    ChatMessage,
    LLMResponse,
    TokenUsage,
)
from ai.providers.base import LLMProvider


logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI-backed LLM provider."""

    CONNECT_TIMEOUT = 10.0
    WRITE_TIMEOUT = 10.0
    POOL_TIMEOUT = 10.0

    def __init__(
        self,
        *,
        api_key: str,
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=settings.OPENAI_BASE_URL,
            timeout=(
                self.CONNECT_TIMEOUT,
                settings.OPENAI_READ_TIMEOUT,
                self.WRITE_TIMEOUT,
                self.POOL_TIMEOUT,
            ),
            max_retries=2,
        )

        logger.info(
            "OpenAI provider initialized",
            extra={
                "base_url": settings.OPENAI_BASE_URL,
                "read_timeout": settings.OPENAI_READ_TIMEOUT,
            },
        )

    @staticmethod
    def _build_messages(
        messages: list[ChatMessage],
    ) -> list[dict[str, str]]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

    @staticmethod
    def _usage(response) -> TokenUsage | None:
        usage = getattr(response, "usage", None)

        if usage is None:
            return None

        return TokenUsage(
            input_tokens=getattr(
                usage,
                "prompt_tokens",
                0,
            ),
            output_tokens=getattr(
                usage,
                "completion_tokens",
                0,
            ),
        )

    @staticmethod
    def _log_api_error(
        exc: Exception,
        *,
        model: str,
    ) -> None:
        """
        Log as much useful information as possible without
        exposing the API key.
        """

        logger.error(
            "OpenAI API request failed",
            extra={
                "model": model,
                "base_url": settings.OPENAI_BASE_URL,
                "error_type": type(exc).__name__,
                "status_code": getattr(
                    exc,
                    "status_code",
                    None,
                ),
                "request_id": getattr(
                    exc,
                    "request_id",
                    None,
                ),
                "response": str(exc),
            },
            exc_info=True,
        )

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        start_time = perf_counter()

        logger.info(
            "OpenAI request started",
            extra={
                "model": model,
                "base_url": settings.OPENAI_BASE_URL,
                "message_count": len(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=self._build_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            choice = response.choices[0]

            logger.info(
                "OpenAI request succeeded",
                extra={
                    "model": model,
                    "finish_reason": choice.finish_reason,
                },
            )

            return LLMResponse(
                content=choice.message.content or "",
                model=model,
                provider="openai",
                usage=self._usage(response),
                finish_reason=choice.finish_reason,
            )

        except AuthenticationError as exc:
            self._log_api_error(exc, model=model)

            raise LLMAuthenticationError(
                "OpenAI authentication failed"
            ) from exc

        except RateLimitError as exc:
            self._log_api_error(exc, model=model)

            raise LLMRateLimitError(
                "OpenAI rate limit exceeded"
            ) from exc

        except APITimeoutError as exc:
            self._log_api_error(exc, model=model)

            raise LLMTimeoutError(
                "OpenAI request timed out"
            ) from exc

        except APIConnectionError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                "OpenAI connection failed"
            ) from exc

        except InternalServerError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                "OpenAI internal server error"
            ) from exc

        except APIStatusError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                f"OpenAI request failed with status "
                f"{exc.status_code}"
            ) from exc

        except APIError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                "OpenAI API request failed"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected OpenAI provider error",
                extra={
                    "model": model,
                    "base_url": settings.OPENAI_BASE_URL,
                    "error_type": type(exc).__name__,
                },
            )

            raise LLMProviderError(
                "Unexpected OpenAI provider error"
            ) from exc

        finally:
            logger.info(
                "OpenAI request finished",
                extra={
                    "model": model,
                    "duration_ms": round(
                        (perf_counter() - start_time) * 1000,
                        2,
                    ),
                },
            )

    def generate_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        start_time = perf_counter()

        logger.info(
            "OpenAI streaming request started",
            extra={
                "model": model,
                "base_url": settings.OPENAI_BASE_URL,
                "message_count": len(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=self._build_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            logger.info(
                "OpenAI streaming connection established",
                extra={
                    "model": model,
                },
            )

            token_count = 0

            for chunk in stream:
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content

                if content:
                    token_count += 1
                    yield content

            logger.info(
                "OpenAI streaming completed",
                extra={
                    "model": model,
                    "chunks": token_count,
                },
            )

        except AuthenticationError as exc:
            self._log_api_error(exc, model=model)

            raise LLMAuthenticationError(
                "OpenAI authentication failed"
            ) from exc

        except RateLimitError as exc:
            self._log_api_error(exc, model=model)

            raise LLMRateLimitError(
                "OpenAI rate limit exceeded"
            ) from exc

        except APITimeoutError as exc:
            self._log_api_error(exc, model=model)

            raise LLMTimeoutError(
                "OpenAI request timed out"
            ) from exc

        except APIConnectionError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                "OpenAI connection failed"
            ) from exc

        except InternalServerError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                "OpenAI internal server error"
            ) from exc

        except APIStatusError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                f"OpenAI request failed with status "
                f"{exc.status_code}"
            ) from exc

        except APIError as exc:
            self._log_api_error(exc, model=model)

            raise LLMProviderError(
                "OpenAI API request failed"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected OpenAI streaming error",
                extra={
                    "model": model,
                    "base_url": settings.OPENAI_BASE_URL,
                    "error_type": type(exc).__name__,
                },
            )

            raise LLMProviderError(
                "Unexpected OpenAI provider error"
            ) from exc

        finally:
            logger.info(
                "OpenAI streaming request finished",
                extra={
                    "model": model,
                    "duration_ms": round(
                        (perf_counter() - start_time) * 1000,
                        2,
                    ),
                },
            )

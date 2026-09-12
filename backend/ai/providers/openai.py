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
            max_retries=0,
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

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        start_time = perf_counter()

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=self._build_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            choice = response.choices[0]

            return LLMResponse(
                content=choice.message.content or "",
                model=model,
                provider="openai",
                usage=self._usage(response),
                finish_reason=choice.finish_reason,
            )

        except AuthenticationError as exc:
            raise LLMAuthenticationError(
                "OpenAI authentication failed"
            ) from exc

        except RateLimitError as exc:
            raise LLMRateLimitError(
                "OpenAI rate limit exceeded"
            ) from exc

        except APITimeoutError as exc:
            raise LLMTimeoutError(
                "OpenAI request timed out"
            ) from exc

        except APIConnectionError as exc:
            raise LLMProviderError(
                "OpenAI connection failed"
            ) from exc

        except APIStatusError as exc:
            raise LLMProviderError(
                f"OpenAI request failed with status "
                f"{exc.status_code}"
            ) from exc

        except APIError as exc:
            raise LLMProviderError(
                "OpenAI API request failed"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected OpenAI provider error",
                extra={
                    "model": model,
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
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=self._build_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            for chunk in stream:
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content

                if content:
                    yield content

        except AuthenticationError as exc:
            raise LLMAuthenticationError(
                "OpenAI authentication failed"
            ) from exc

        except RateLimitError as exc:
            raise LLMRateLimitError(
                "OpenAI rate limit exceeded"
            ) from exc

        except APITimeoutError as exc:
            raise LLMTimeoutError(
                "OpenAI request timed out"
            ) from exc

        except APIConnectionError as exc:
            raise LLMProviderError(
                "OpenAI connection failed"
            ) from exc

        except APIStatusError as exc:
            raise LLMProviderError(
                f"OpenAI request failed with status "
                f"{exc.status_code}"
            ) from exc

        except APIError as exc:
            raise LLMProviderError(
                "OpenAI API request failed"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected OpenAI streaming error",
                extra={
                    "model": model,
                    "error_type": type(exc).__name__,
                },
            )
            raise LLMProviderError(
                "Unexpected OpenAI provider error"
            ) from exc

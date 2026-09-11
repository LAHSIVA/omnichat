import logging
from collections.abc import Iterator
from time import perf_counter
from django.conf import settings

from openai import (
    APIConnectionError,
    APIError,
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
from ai.domain.types import ChatMessage, LLMResponse, TokenUsage
from ai.providers.base import LLMProvider
from openai import APIStatusError
logger = logging.getLogger(__name__)


class FreeLLMAPIProvider(LLMProvider):
    """OpenAI-compatible provider backed by FreeLLMAPI."""

    CONNECT_TIMEOUT = 10.0
    WRITE_TIMEOUT = 10.0
    POOL_TIMEOUT = 10.0

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=(
                self.CONNECT_TIMEOUT,
                settings.FREELLMAPI_READ_TIMEOUT,
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
    def _get_message_stats(
        messages: list[ChatMessage],
    ) -> tuple[int, int]:
        """Return message count and total character count."""
        return (
            len(messages),
            sum(len(message.content) for message in messages),
        )
    @staticmethod
    def _build_request_kwargs(
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int | None,
        stream: bool = False,
    ) -> dict:
        request_kwargs = {
            "model": model,
            "messages": FreeLLMAPIProvider._build_messages(messages),
            "temperature": temperature,
            "stream": stream,
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        return request_kwargs

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        request_kwargs = self._build_request_kwargs(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message_count, character_count = self._get_message_stats(messages)

        try:
            response = self.client.chat.completions.create(
                **request_kwargs,
            )
        except AuthenticationError as exc:
            raise LLMAuthenticationError(
                "LLM provider authentication failed"
            ) from exc
        except RateLimitError as exc:
            raise LLMRateLimitError(
                "LLM provider rate limit exceeded"
            ) from exc
        except APITimeoutError as exc:
            raise LLMTimeoutError(
                "LLM provider request timed out"
            ) from exc
        except APIConnectionError as exc:
            raise LLMProviderError(
                "LLM provider connection failed"
            ) from exc
        except APIStatusError as exc:
            logger.exception(
                "FreeLLMAPI HTTP error: "
                "status_code=%s model=%s request_id=%s response=%s",
                exc.status_code,
                model,
                getattr(exc, "request_id", None),
                getattr(exc.response, "text", None),
            )

            raise LLMProviderError(
                f"FreeLLMAPI request failed with status {exc.status_code}"
            ) from exc

        except APIError as exc:
            logger.exception(
                "FreeLLMAPI API error: model=%s error=%s",
                model,
                exc,
            )

            raise LLMProviderError(
                "LLM provider request failed"
            ) from exc

        usage = None

        if response.usage is not None:
            usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

        content = response.choices[0].message.content or ""

        logger.info(
            "FreeLLMAPI generation request completed: "
            "model=%s message_count=%d character_count=%d",
            model,
            message_count,
            character_count,
        )

        return LLMResponse(
            content=content,
            model=response.model,
            provider="freellmapi",
            usage=usage,
            finish_reason=response.choices[0].finish_reason,
        )

    def generate_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        request_kwargs = self._build_request_kwargs(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        message_count, character_count = self._get_message_stats(messages)

        start_time = perf_counter()
        chunks_received = 0

        logger.info(
            "FreeLLMAPI generation request started: "
            "model=%s message_count=%d character_count=%d",
            model,
            message_count,
            character_count,
        )

        logger.info(
            "FreeLLMAPI request details: roles=%s content_lengths=%s",
            [message["role"] for message in request_kwargs["messages"]],
            [len(message["content"]) for message in request_kwargs["messages"]],
        )

        try:
            response = self.client.chat.completions.create(
                **request_kwargs,
            )

            logger.info(
                "FreeLLMAPI streaming connection established",
                extra={
                    "model": model,
                    "duration_ms": round(
                        (perf_counter() - start_time) * 1000,
                        2,
                    ),
                },
            )

            for chunk in response:
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content

                if not content:
                    continue

                chunks_received += 1

                if chunks_received == 1:
                    logger.info(
                        "FreeLLMAPI first stream chunk received",
                        extra={
                            "model": model,
                            "duration_ms": round(
                                (perf_counter() - start_time) * 1000,
                                2,
                            ),
                        },
                    )

                yield content

        except AuthenticationError as exc:
            logger.exception(
                "FreeLLMAPI authentication error: model=%s",
                model,
            )
            raise LLMAuthenticationError(
                "LLM provider authentication failed"
            ) from exc

        except RateLimitError as exc:
            logger.exception(
                "FreeLLMAPI rate limit error: model=%s",
                model,
            )
            raise LLMRateLimitError(
                "LLM provider rate limit exceeded"
            ) from exc

        except APITimeoutError as exc:
            logger.exception(
                "FreeLLMAPI timeout: model=%s",
                model,
            )
            raise LLMTimeoutError(
                "LLM provider request timed out"
            ) from exc

        except APIConnectionError as exc:
            logger.exception(
                "FreeLLMAPI connection error: model=%s",
                model,
            )
            raise LLMProviderError(
                "LLM provider connection failed"
            ) from exc

        except APIStatusError as exc:
            logger.exception(
                "FreeLLMAPI HTTP error: "
                "status_code=%s model=%s request_id=%s response=%s",
                exc.status_code,
                model,
                getattr(exc, "request_id", None),
                getattr(exc.response, "text", None),
            )

            raise LLMProviderError(
                f"FreeLLMAPI request failed with status {exc.status_code}"
            ) from exc

        except APIError as exc:
            logger.exception(
                "FreeLLMAPI API error: model=%s error=%s",
                model,
                exc,
            )

            raise LLMProviderError(
                "LLM provider request failed"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected FreeLLMAPI streaming error: "
                "model=%s error_type=%s",
                model,
                type(exc).__name__,
            )
            raise LLMProviderError(
                "Unexpected LLM provider error"
            ) from exc

        finally:
            logger.info(
                "FreeLLMAPI streaming request finished",
                extra={
                    "model": model,
                    "duration_ms": round(
                        (perf_counter() - start_time) * 1000,
                        2,
                    ),
                    "chunks_received": chunks_received,
                },
            )

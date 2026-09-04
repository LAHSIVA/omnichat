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
from collections.abc import Iterator
from collections.abc import Iterator
class FreeLLMAPIProvider(LLMProvider):
    """OpenAI-compatible provider backed by FreeLLMAPI."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        request_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

        request_kwargs = {
            "model": model,
            "messages": request_messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

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
        except APIError as exc:
            raise LLMProviderError(
                "LLM provider request failed"
            ) from exc

        usage = None

        if response.usage is not None:
            usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

        return LLMResponse(
            content=response.choices[0].message.content or "",
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
        request_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
        ]

        request_kwargs = {
            "model": model,
            "messages": request_messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        try:
            response = self.client.chat.completions.create(
                **request_kwargs
            )

            for chunk in response:
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content

                if content:
                    yield content

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
        except APIError as exc:
            raise LLMProviderError(
                "LLM provider request failed"
            ) from exc
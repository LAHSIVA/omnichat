from openai import OpenAI

from ai.domain.types import ChatMessage, LLMResponse, TokenUsage
from ai.providers.base import LLMProvider


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

        response = self.client.chat.completions.create(
            **request_kwargs,
        )

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
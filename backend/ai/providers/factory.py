from django.conf import settings

from ai.providers.base import LLMProvider
from ai.providers.fake import FakeLLMProvider
from ai.providers.freellmapi import FreeLLMAPIProvider


def create_llm_provider() -> LLMProvider:
    provider_name = settings.AI_PROVIDER

    if provider_name == "fake":
        return FakeLLMProvider()

    if provider_name == "freellmapi":
        if not settings.FREELLMAPI_API_KEY:
            raise ValueError(
                "FREELLMAPI_API_KEY is required "
                "when AI_PROVIDER=freellmapi"
            )

        return FreeLLMAPIProvider(
            api_key=settings.FREELLMAPI_API_KEY,
            base_url=settings.FREELLMAPI_BASE_URL,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider_name}"
    )
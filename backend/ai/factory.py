from django.conf import settings

from ai.gateway import LLMGateway
from ai.providers.base import LLMProvider
from ai.providers.factory import create_llm_provider
from ai.providers.freellmapi import FreeLLMAPIProvider


def create_llm_gateway(model: str | None = None) -> LLMGateway:
    selected_model = model or "auto"

    primary_provider = create_llm_provider()

    fallback_provider: LLMProvider | None = None

    if settings.FREELLMAPI_API_KEY:
        fallback_provider = FreeLLMAPIProvider(
            api_key=settings.FREELLMAPI_API_KEY,
            base_url=settings.FREELLMAPI_BASE_URL,
        )

    return LLMGateway(
        provider=primary_provider,
        model=selected_model,
        fallback_provider=fallback_provider,
        fallback_model="auto",
        enable_fallback=(
            fallback_provider is not None
        ),
    )

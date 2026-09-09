from django.conf import settings

from ai.gateway import LLMGateway
from ai.providers.factory import create_llm_provider


def create_llm_gateway(model: str | None = None) -> LLMGateway:
    selected_model = model or settings.AI_MODEL

    provider = create_llm_provider()

    return LLMGateway(
        provider=provider,
        model=selected_model,
        enable_fallback=True,
    )

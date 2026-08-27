from django.conf import settings

from ai.gateway import LLMGateway
from ai.providers.factory import create_llm_provider


def create_llm_gateway() -> LLMGateway:
    provider = create_llm_provider()

    return LLMGateway(
        provider=provider,
        model=settings.AI_MODEL,
    )
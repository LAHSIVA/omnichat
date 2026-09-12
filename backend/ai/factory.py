from django.conf import settings

from ai.gateway import LLMGateway
from ai.providers.factory import create_llm_provider


def create_llm_gateway(model: str | None = None) -> LLMGateway:
    """
    Create the LLM gateway.

    For the current demo, every UI model selection uses the
    single configured OpenAI model from settings.AI_MODEL.

    The frontend can continue sending:
        auto
        gemini-3.5-flash-lite
        gemini-3.6-flash
        claude-sonnet-4-5
        fusion

    But all of them are routed to the same actual provider model,
    currently configured as gpt-4o-mini.
    """

    primary_provider = create_llm_provider()

    # IMPORTANT:
    # Do not send UI model IDs such as "auto" or "fusion"
    # directly to OpenAI.
    #
    # The actual provider model comes from AI_MODEL.
    selected_model = settings.AI_MODEL

    return LLMGateway(
        provider=primary_provider,
        model=selected_model,
        enable_fallback=False,
    )

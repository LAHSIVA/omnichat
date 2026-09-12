from collections.abc import Sequence

from django.conf import settings


class ModelFallbackPolicy:
    """Resolve an ordered list of models for transient LLM failures."""

    @classmethod
    def candidates(cls, model: str | None) -> Sequence[str]:
        """
        Return the model to use.

        For the current demo, every frontend model selection is mapped
        to the configured backend model. This prevents UI-only model
        names such as 'auto', 'fast', 'maximum', etc. from being sent
        directly to OpenAI.
        """

        return (settings.AI_MODEL,)

from collections.abc import Sequence

from django.conf import settings


class ModelFallbackPolicy:
    """Resolve logical application model names to provider models."""

    _FALLBACKS: dict[str, tuple[str, ...]] = {
        "auto": (),
        "gemini-3.5-flash-lite": (
            "gemini-3.5-flash-lite",
        ),
        "gemini-3.6-flash": (
            "gemini-3.6-flash",
        ),
        "claude-sonnet-4-5": (
            "claude-sonnet-4-5",
        ),
        "fusion": (
            "fusion",
        ),
    }

    @classmethod
    def candidates(cls, model: str | None) -> Sequence[str]:
        """
        Return provider models to try.

        'auto' means use the configured default model rather
        than sending the literal string 'auto' to the provider.
        """

        selected_model = model or "auto"

        if selected_model == "auto":
            return (settings.AI_MODEL,)

        return cls._FALLBACKS.get(
            selected_model,
            (selected_model,),
        )

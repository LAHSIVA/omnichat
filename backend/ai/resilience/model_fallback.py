from collections.abc import Sequence


class ModelFallbackPolicy:
    """Resolve an ordered list of models for transient LLM failures."""

    _FALLBACKS: dict[str, tuple[str, ...]] = {
        "auto": ("auto",),
        "gemini-3.5-flash-lite": (
            "gemini-3.5-flash-lite",
            "auto",
        ),
        "gemini-3.6-flash": (
            "gemini-3.6-flash",
            "auto",
        ),
        "claude-sonnet-4-5": (
            "claude-sonnet-4-5",
            "auto",
        ),
        "fusion": (
            "fusion",
            "auto",
        ),
    }

    @classmethod
    def candidates(cls, model: str) -> Sequence[str]:
        """Return models to try in priority order."""
        return cls._FALLBACKS.get(model, (model, "auto"))

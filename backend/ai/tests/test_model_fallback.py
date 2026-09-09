from ai.resilience.model_fallback import ModelFallbackPolicy


def test_auto_has_no_fallback():
    assert ModelFallbackPolicy.candidates("auto") == ("auto",)


def test_fast_falls_back_to_auto():
    assert ModelFallbackPolicy.candidates(
        "gemini-3.5-flash-lite"
    ) == (
        "gemini-3.5-flash-lite",
        "auto",
    )


def test_balanced_falls_back_to_auto():
    assert ModelFallbackPolicy.candidates(
        "gemini-3.6-flash"
    ) == (
        "gemini-3.6-flash",
        "auto",
    )


def test_quality_falls_back_to_auto():
    assert ModelFallbackPolicy.candidates(
        "claude-sonnet-4-5"
    ) == (
        "claude-sonnet-4-5",
        "auto",
    )


def test_maximum_falls_back_to_auto():
    assert ModelFallbackPolicy.candidates(
        "fusion"
    ) == (
        "fusion",
        "auto",
    )


def test_unknown_model_falls_back_to_auto():
    assert ModelFallbackPolicy.candidates(
        "unknown-model"
    ) == (
        "unknown-model",
        "auto",
    )

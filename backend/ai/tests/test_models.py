import pytest

from ai.models import AVAILABLE_MODELS, get_model


def test_available_models_have_unique_ids():
    model_ids = [model.id for model in AVAILABLE_MODELS]

    assert len(model_ids) == len(set(model_ids))


@pytest.mark.parametrize(
    "model_id",
    [
        "auto",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "claude-sonnet-4-5",
        "fusion",
    ],
)
def test_get_model_returns_registered_model(model_id):
    model = get_model(model_id)

    assert model.id == model_id


def test_get_model_rejects_unknown_model():
    with pytest.raises(ValueError, match="Unsupported model"):
        get_model("not-a-real-model")

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelDefinition:
    id: str
    display_name: str
    description: str


AVAILABLE_MODELS = (
    ModelDefinition(
        id="auto",
        display_name="Auto",
        description="Automatically select the best available model.",
    ),
    ModelDefinition(
        id="gemini-3.5-flash-lite",
        display_name="Fast",
        description="Fast and lightweight responses.",
    ),
    ModelDefinition(
        id="gemini-3.6-flash",
        display_name="Balanced",
        description="Balanced speed and response quality.",
    ),
    ModelDefinition(
        id="claude-sonnet-4-5",
        display_name="Quality",
        description="Higher-quality responses for complex questions.",
    ),
    ModelDefinition(
        id="fusion",
        display_name="Maximum",
        description="Uses multiple models and synthesizes the result.",
    ),
)


def get_model(model_id: str) -> ModelDefinition:
    for model in AVAILABLE_MODELS:
        if model.id == model_id:
            return model

    raise ValueError(f"Unsupported model: {model_id}")

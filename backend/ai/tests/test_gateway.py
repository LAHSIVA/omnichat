from ai.domain.types import ChatMessage
from ai.gateway import LLMGateway
from ai.providers.fake import FakeLLMProvider


def test_gateway_delegates_to_provider():
    gateway = LLMGateway(
        provider=FakeLLMProvider(),
        model="fake-model",
    )

    response = gateway.generate(
        [
            ChatMessage(
                role="user",
                content="What is RAG?",
            )
        ]
    )

    assert response.content == "This is a fake AI response."
    assert response.provider == "fake"
    assert response.model == "fake-model"


def test_gateway_uses_configured_model():
    gateway = LLMGateway(
        provider=FakeLLMProvider(),
        model="custom-test-model",
    )

    response = gateway.generate(
        [
            ChatMessage(
                role="user",
                content="Explain embeddings.",
            )
        ]
    )

    assert response.model == "custom-test-model"
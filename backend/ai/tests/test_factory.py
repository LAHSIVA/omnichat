import pytest
from django.test import override_settings

from ai.factory import create_llm_gateway
from ai.gateway import LLMGateway
from ai.providers.factory import create_llm_provider
from ai.providers.fake import FakeLLMProvider
from unittest.mock import patch

from ai.factory import create_llm_gateway

@override_settings(AI_PROVIDER="fake")
def test_factory_creates_fake_provider():
    provider = create_llm_provider()

    assert isinstance(provider, FakeLLMProvider)


@override_settings(AI_PROVIDER="unsupported-provider")
def test_factory_rejects_unsupported_provider():
    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider",
    ):
        create_llm_provider()


@override_settings(
    AI_PROVIDER="fake",
    AI_MODEL="test-model",
)
def test_factory_creates_configured_gateway():
    gateway = create_llm_gateway()

    assert isinstance(gateway, LLMGateway)
    assert gateway.model == "test-model"
    assert isinstance(gateway.provider, FakeLLMProvider)


def test_create_llm_gateway_uses_configured_model():
    with patch("ai.factory.create_llm_provider") as create_provider:
        provider = object()
        create_provider.return_value = provider

        gateway = create_llm_gateway()

    assert gateway.provider is provider


def test_create_llm_gateway_accepts_selected_model():
    with patch("ai.factory.create_llm_provider") as create_provider:
        provider = object()
        create_provider.return_value = provider

        gateway = create_llm_gateway(model="gemini-3.6-flash")

    assert gateway.provider is provider
    assert gateway.model == "gemini-3.6-flash"

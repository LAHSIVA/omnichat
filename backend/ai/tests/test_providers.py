from types import SimpleNamespace

import httpx
import pytest

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)

from ai.domain.types import ChatMessage
from ai.providers.fake import FakeLLMProvider
from ai.providers.freellmapi import FreeLLMAPIProvider


def test_freellmapi_provider_omits_max_tokens_when_not_provided(
    monkeypatch,
):
    captured_kwargs = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured_kwargs.update(kwargs)

            return SimpleNamespace(
                model="gemini-3-flash-preview",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Test response",
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=None,
            )

    class FakeClient:
        def __init__(self):
            self.chat = SimpleNamespace(
                completions=FakeCompletions(),
            )

    fake_client = FakeClient()

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = fake_client

    response = provider.generate(
        [
            ChatMessage(
                role="user",
                content="Hello",
            )
        ],
        model="gemini-3-flash-preview",
    )

    assert response.content == "Test response"

    assert "max_tokens" not in captured_kwargs

def test_freellmapi_provider_sends_max_tokens_when_provided():
    captured_kwargs = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured_kwargs.update(kwargs)

            return SimpleNamespace(
                model="gemini-3-flash-preview",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Test response",
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=None,
            )

    class FakeClient:
        def __init__(self):
            self.chat = SimpleNamespace(
                completions=FakeCompletions(),
            )

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = FakeClient()

    provider.generate(
        [
            ChatMessage(
                role="user",
                content="Hello",
            )
        ],
        model="gemini-3-flash-preview",
        max_tokens=100,
    )

    assert captured_kwargs["max_tokens"] == 100

class FailingCompletions:
    def __init__(self, error):
        self.error = error

    def create(self, **kwargs):
        raise self.error


class FailingClient:
    def __init__(self, error):
        self.chat = SimpleNamespace(
            completions=FailingCompletions(error),
        )

def test_freellmapi_authentication_error_is_translated():
    request = httpx.Request(
    "POST",
    "http://test-server/v1/chat/completions",
    )

    response = httpx.Response(
        401,
        request=request,
    )

    error = AuthenticationError(
        "Invalid API key",
        response=response,
        body={"error": "invalid_api_key"},
    )

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = FailingClient(error)

    with pytest.raises(LLMAuthenticationError):
        provider.generate(
            [
                ChatMessage(
                    role="user",
                    content="Hello",
                )
            ],
            model="gemini-3-flash-preview",
        )

def test_freellmapi_rate_limit_error_is_translated():
    request = httpx.Request(
        "POST",
        "http://test-server/v1/chat/completions",
    )

    response = httpx.Response(
        429,
        request=request,
    )

    error = RateLimitError(
        "Rate limit exceeded",
        response=response,
        body={"error": "rate_limit"},
    )

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = FailingClient(error)

    with pytest.raises(LLMRateLimitError):
        provider.generate(
            [
                ChatMessage(
                    role="user",
                    content="Hello",
                )
            ],
            model="gemini-3-flash-preview",
        )

def test_freellmapi_timeout_error_is_translated():
    error = APITimeoutError(request=None)

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = FailingClient(error)

    with pytest.raises(LLMTimeoutError):
        provider.generate(
            [
                ChatMessage(
                    role="user",
                    content="Hello",
                )
            ],
            model="gemini-3-flash-preview",
        )

def test_freellmapi_connection_error_is_translated():
    error = APIConnectionError(request=None)

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = FailingClient(error)

    with pytest.raises(LLMProviderError):
        provider.generate(
            [
                ChatMessage(
                    role="user",
                    content="Hello",
                )
            ],
            model="gemini-3-flash-preview",
        )
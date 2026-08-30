import pytest

from ai.domain.exceptions import LLMRateLimitError
from ai.domain.types import ChatMessage, LLMResponse
from ai.gateway import LLMGateway
from ai.resilience.retry import RetryPolicy
from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
)
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

def test_gateway_retries_rate_limit():
    calls = 0

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            nonlocal calls
            calls += 1

            if calls == 1:
                raise LLMRateLimitError("Rate limit exceeded")

            return LLMResponse(
                content="Success after retry",
                model=model,
                provider="fake",
                usage=None,
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=2,
            backoff_seconds=0,
        ),
    )

    response = gateway.generate(
        [
            ChatMessage(
                role="user",
                content="Hello",
            )
        ],
    )

    assert response.content == "Success after retry"
    assert calls == 2

def test_gateway_does_not_retry_authentication_error():
    calls = 0

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            nonlocal calls
            calls += 1

            raise LLMAuthenticationError(
                "Invalid credentials"
            )

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=2,
            backoff_seconds=0,
        ),
    )

    with pytest.raises(
        LLMAuthenticationError,
        match="Invalid credentials",
    ):
        gateway.generate(
            [
                ChatMessage(
                    role="user",
                    content="Hello",
                )
            ],
        )

    assert calls == 1


def test_gateway_raises_after_rate_limit_retries_are_exhausted():
    calls = 0

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            nonlocal calls
            calls += 1

            raise LLMRateLimitError(
                "Rate limit exceeded"
            )

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=2,
            backoff_seconds=0,
        ),
    )

    with pytest.raises(
        LLMRateLimitError,
        match="Rate limit exceeded",
    ):
        gateway.generate(
            [
                ChatMessage(
                    role="user",
                    content="Hello",
                )
            ],
        )

    assert calls == 2


def test_gateway_success_calls_provider_once():
    calls = 0

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            nonlocal calls
            calls += 1

            return LLMResponse(
                content="Direct success",
                model=model,
                provider="fake",
                usage=None,
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=2,
            backoff_seconds=0,
        ),
    )

    response = gateway.generate(
        [
            ChatMessage(
                role="user",
                content="Hello",
            )
        ],
    )

    assert response.content == "Direct success"
    assert response.model == "fake-model"
    assert response.provider == "fake"
    assert response.finish_reason == "stop"

    assert calls == 1
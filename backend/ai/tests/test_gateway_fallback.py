import pytest

from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from ai.domain.types import ChatMessage, LLMResponse
from ai.gateway import LLMGateway
from ai.resilience.retry import RetryPolicy


MESSAGES = [
    ChatMessage(
        role="user",
        content="Hello",
    )
]


def test_gateway_falls_back_after_rate_limit():
    calls = []

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            calls.append(model)

            if model == "primary":
                raise LLMRateLimitError("Rate limit exceeded")

            return LLMResponse(
                content="Fallback success",
                model=model,
                provider="fake",
                usage=None,
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="primary",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
        enable_fallback=True,
    )

    response = gateway.generate(MESSAGES)

    assert response.content == "Fallback success"
    assert response.model == "auto"
    assert calls == ["primary", "auto"]


@pytest.mark.parametrize(
    "exception",
    [
        LLMTimeoutError("Provider timed out"),
        LLMProviderError("Provider failed"),
    ],
)
def test_gateway_falls_back_after_transient_error(exception):
    calls = []

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            calls.append(model)

            if model == "primary":
                raise exception

            return LLMResponse(
                content="Fallback success",
                model=model,
                provider="fake",
                usage=None,
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="primary",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
        enable_fallback=True,
    )

    response = gateway.generate(MESSAGES)

    assert response.model == "auto"
    assert response.content == "Fallback success"
    assert calls == ["primary", "auto"]


def test_gateway_does_not_fallback_on_authentication_error():
    calls = []

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            calls.append(model)
            raise LLMAuthenticationError("Invalid credentials")

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="primary",
        retry_policy=RetryPolicy(
            max_attempts=2,
            backoff_seconds=0,
        ),
        enable_fallback=True,
    )

    with pytest.raises(
        LLMAuthenticationError,
        match="Invalid credentials",
    ):
        gateway.generate(MESSAGES)

    assert calls == ["primary"]


def test_gateway_does_not_fallback_after_success():
    calls = []

    class FakeProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            calls.append(model)

            return LLMResponse(
                content="Primary success",
                model=model,
                provider="fake",
                usage=None,
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="primary",
        enable_fallback=True,
    )

    response = gateway.generate(MESSAGES)

    assert response.content == "Primary success"
    assert response.model == "primary"
    assert calls == ["primary"]

import pytest

from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from ai.gateway import LLMGateway
from ai.resilience.retry import RetryPolicy


MESSAGES = []


def test_stream_falls_back_before_first_token_on_rate_limit():
    calls = []

    class FakeProvider:
        def generate_stream(
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

            yield "Fallback response"

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="primary",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
        enable_fallback=True,
    )

    chunks = list(gateway.generate_stream(MESSAGES))

    assert "".join(chunks) == "Fallback response"
    assert calls == ["primary", "auto"]


@pytest.mark.parametrize(
    "exception",
    [
        LLMTimeoutError("Provider timed out"),
        LLMProviderError("Provider failed"),
    ],
)
def test_stream_falls_back_before_first_token_on_transient_error(
    exception,
):
    calls = []

    class FakeProvider:
        def generate_stream(
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

            yield "Fallback response"

    gateway = LLMGateway(
        provider=FakeProvider(),
        model="primary",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
        enable_fallback=True,
    )

    chunks = list(gateway.generate_stream(MESSAGES))

    assert "".join(chunks) == "Fallback response"
    assert calls == ["primary", "auto"]


def test_stream_does_not_fallback_after_first_token():
    calls = []

    class FakeProvider:
        def generate_stream(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            calls.append(model)

            if model == "primary":
                yield "Partial response"
                raise LLMTimeoutError("Provider timed out")

            yield "Fallback response"

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
        LLMTimeoutError,
        match="Provider timed out",
    ):
        list(gateway.generate_stream(MESSAGES))

    assert calls == ["primary"]


def test_stream_does_not_fallback_on_authentication_error():
    calls = []

    class FakeProvider:
        def generate_stream(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            calls.append(model)
            raise LLMAuthenticationError("Invalid credentials")
            yield

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
        list(gateway.generate_stream(MESSAGES))

    assert calls == ["primary"]

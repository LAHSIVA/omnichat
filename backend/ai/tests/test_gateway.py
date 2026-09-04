import pytest

from ai.domain.exceptions import LLMRateLimitError
from ai.domain.types import ChatMessage, LLMResponse
from ai.gateway import LLMGateway
from ai.resilience.retry import RetryPolicy
from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
)
from ai.domain.types import (
    ChatMessage,
    LLMResponse,
    TokenUsage,
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

def test_gateway_logs_request_start(caplog):
    gateway = LLMGateway(
        provider=FakeLLMProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
    )

    with caplog.at_level("INFO", logger="ai.gateway"):
        gateway.generate(
            [
                ChatMessage(
                    role="user",
                    content="Secret user message",
                )
            ],
        )

    assert "LLM request started" in caplog.text

    record = next(
        record
        for record in caplog.records
        if record.message == "LLM request started"
    )

    assert record.model == "fake-model"
    assert record.provider == "FakeLLMProvider"
    assert "Secret user message" not in caplog.text


def test_gateway_logs_request_completion(caplog):
    gateway = LLMGateway(
        provider=FakeLLMProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
    )

    with caplog.at_level("INFO", logger="ai.gateway"):
        gateway.generate(
            [
                ChatMessage(
                    role="user",
                    content="Secret user message",
                )
            ],
        )

    record = next(
        record
        for record in caplog.records
        if record.message == "LLM request completed"
    )

    assert record.provider == "fake"
    assert record.model == "fake-model"
    assert record.duration_ms >= 0
    assert "Secret user message" not in caplog.text


def test_gateway_logs_request_failure(caplog):
    class FailingProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            raise LLMProviderError(
                "Sensitive internal provider details"
            )

    gateway = LLMGateway(
        provider=FailingProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
    )

    with caplog.at_level("ERROR", logger="ai.gateway"):
        with pytest.raises(
            LLMProviderError,
            match="Sensitive internal provider details",
        ):
            gateway.generate(
                [
                    ChatMessage(
                        role="user",
                        content="Secret user message",
                    )
                ],
            )

    record = next(
        record
        for record in caplog.records
        if record.message == "LLM request failed"
    )

    assert record.model == "fake-model"
    assert record.error_type == "LLMProviderError"
    assert record.duration_ms >= 0

    assert "Sensitive internal provider details" not in caplog.text
    assert "Secret user message" not in caplog.text

def test_gateway_logs_retry_then_completion_without_failure(
    caplog,
):
    calls = 0

    class RateLimitedProvider:
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
                raise LLMRateLimitError(
                    "Rate limit exceeded"
                )

            return LLMResponse(
                content="Success after retry",
                model=model,
                provider="fake",
                usage=None,
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=RateLimitedProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=2,
            backoff_seconds=0,
        ),
    )

    with caplog.at_level(
        "INFO",
        logger="ai.gateway",
    ):
        with caplog.at_level("INFO"):
            response = gateway.generate(
                [
                    ChatMessage(
                        role="user",
                        content="Hello",
                    )
                ],
            )

    assert response.content == "Success after retry"

    messages = [
        record.message
        for record in caplog.records
    ]

    assert "LLM request started" in messages
    assert "LLM request retrying" in messages
    assert "LLM request completed" in messages
    assert "LLM request failed" not in messages

    retry_record = next(
        record
        for record in caplog.records
        if record.message == "LLM request retrying"
    )

    assert retry_record.attempt == 1
    assert retry_record.next_attempt == 2

    completion_record = next(
        record
        for record in caplog.records
        if record.message == "LLM request completed"
    )

    assert completion_record.model == "fake-model"
    assert completion_record.provider == "fake"

    assert "Rate limit exceeded" not in caplog.text

def test_gateway_logs_token_usage(caplog):
    class TokenProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            return LLMResponse(
                content="Response with usage",
                model=model,
                provider="fake",
                usage=TokenUsage(
                    input_tokens=25,
                    output_tokens=10,
                ),
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=TokenProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
    )

    with caplog.at_level("INFO", logger="ai.gateway"):
        gateway.generate(
            [
                ChatMessage(
                    role="user",
                    content="Secret prompt",
                )
            ],
        )

    record = next(
        record
        for record in caplog.records
        if record.message == "LLM request completed"
    )

    assert record.input_tokens == 25
    assert record.output_tokens == 10
    assert record.duration_ms >= 0

    assert "Secret prompt" not in caplog.text

def test_gateway_logs_missing_token_usage_safely(caplog):
    class NoUsageProvider:
        def generate(
            self,
            messages,
            *,
            model,
            temperature=0.2,
            max_tokens=None,
        ):
            return LLMResponse(
                content="Response without usage",
                model=model,
                provider="fake",
                usage=None,
                finish_reason="stop",
            )

    gateway = LLMGateway(
        provider=NoUsageProvider(),
        model="fake-model",
        retry_policy=RetryPolicy(
            max_attempts=1,
            backoff_seconds=0,
        ),
    )

    with caplog.at_level("INFO", logger="ai.gateway"):
        response = gateway.generate(
            [
                ChatMessage(
                    role="user",
                    content="Hello",
                )
            ],
        )

    assert response.content == "Response without usage"

    record = next(
        record
        for record in caplog.records
        if record.message == "LLM request completed"
    )

    assert record.input_tokens is None
    assert record.output_tokens is None
    assert record.duration_ms >= 0

def test_gateway_streams_provider_response():
    gateway = LLMGateway(
        provider=FakeLLMProvider(),
        model="fake-model",
    )

    chunks = list(
        gateway.generate_stream(
            [], 
        )
    )

    assert "".join(chunks) == "This is a fake AI response."
import pytest
import ai.resilience.retry as retry_module

from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from ai.resilience.retry import RetryPolicy

def test_retry_policy_returns_success_without_retrying():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        return "success"

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=0,
    )

    result = policy.execute(operation)

    assert result == "success"
    assert calls == 1

def test_retry_policy_retries_rate_limit_then_succeeds():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        if calls == 1:
            raise LLMRateLimitError("Rate limit exceeded")

        return "success"

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=0,
    )

    result = policy.execute(operation)

    assert result == "success"
    assert calls == 2

def test_retry_policy_raises_after_max_attempts():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        raise LLMRateLimitError("Rate limit exceeded")

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=0,
    )

    with pytest.raises(
        LLMRateLimitError,
        match="Rate limit exceeded",
    ):
        policy.execute(operation)

    assert calls == 2

def test_retry_policy_does_not_retry_authentication_error():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        raise LLMAuthenticationError("Invalid credentials")

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=0,
    )

    with pytest.raises(
        LLMAuthenticationError,
        match="Invalid credentials",
    ):
        policy.execute(operation)

    assert calls == 1

def test_retry_policy_does_not_retry_timeout():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        raise LLMTimeoutError("Provider timed out")

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=0,
    )

    with pytest.raises(
        LLMTimeoutError,
        match="Provider timed out",
    ):
        policy.execute(operation)

    assert calls == 1

def test_retry_policy_does_not_retry_provider_error():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        raise LLMProviderError("Provider unavailable")

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=0,
    )

    with pytest.raises(
        LLMProviderError,
        match="Provider unavailable",
    ):
        policy.execute(operation)

    assert calls == 1

def test_retry_policy_waits_before_retrying(monkeypatch):
    calls = 0
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        retry_module,
        "sleep",
        fake_sleep,
    )

    def operation():
        nonlocal calls
        calls += 1

        if calls == 1:
            raise LLMRateLimitError("Rate limit exceeded")

        return "success"

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=1.5,
    )

    result = policy.execute(operation)

    assert result == "success"
    assert calls == 2
    assert sleep_calls == [1.5]

def test_retry_policy_rejects_invalid_max_attempts():
    with pytest.raises(
        ValueError,
        match="max_attempts must be at least 1",
    ):
        RetryPolicy(
            max_attempts=0,
            backoff_seconds=0,
        )

def test_retry_policy_rejects_negative_backoff():
    with pytest.raises(
        ValueError,
        match="backoff_seconds cannot be negative",
    ):
        RetryPolicy(
            max_attempts=2,
            backoff_seconds=-1,
        )

def test_retry_policy_logs_retry(caplog):
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        if calls == 1:
            raise LLMRateLimitError("Rate limit exceeded")

        return "success"

    policy = RetryPolicy(
        max_attempts=2,
        backoff_seconds=0,
    )

    with caplog.at_level(
        "WARNING",
        logger="ai.resilience.retry",
    ):
        result = policy.execute(operation)

    assert result == "success"

    record = next(
        record
        for record in caplog.records
        if record.message == "LLM request retrying"
    )

    assert record.attempt == 1
    assert record.next_attempt == 2

    assert "Rate limit exceeded" not in caplog.text
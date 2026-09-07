import logging
from collections.abc import Callable
from time import sleep
from typing import TypeVar

from ai.domain.exceptions import LLMRateLimitError

T = TypeVar("T")

logger = logging.getLogger(__name__)


class RetryPolicy:
    """Retry rate-limited operations with configurable backoff."""

    def __init__(
        self,
        *,
        max_attempts: int = 2,
        backoff_seconds: float = 1.0,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")

        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds

    def execute(self, operation: Callable[[], T]) -> T:
        """Execute an operation, retrying only rate-limit failures."""
        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()

            except LLMRateLimitError:
                if attempt >= self.max_attempts:
                    raise

                logger.warning(
                    "LLM request retrying",
                    extra={
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                        "max_attempts": self.max_attempts,
                    },
                )

                self.sleep()

        raise RuntimeError(
            "Retry policy exhausted without returning or raising."
        )

    def sleep(self) -> None:
        """Wait before the next retry attempt."""
        sleep(self.backoff_seconds)

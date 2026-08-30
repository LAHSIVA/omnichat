from collections.abc import Callable
from time import sleep
from typing import TypeVar
import logging
from ai.domain.exceptions import LLMRateLimitError
logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryPolicy:
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

    def execute(
        self,
        operation: Callable[[], T],
    ) -> T:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()

            except LLMRateLimitError:
                if attempt == self.max_attempts:
                    raise

                logger.warning(
                    "LLM request retrying",
                    extra={
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                    },
                )

                sleep(self.backoff_seconds)
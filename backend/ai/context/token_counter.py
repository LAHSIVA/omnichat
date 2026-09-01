from abc import ABC, abstractmethod

from ai.domain.types import ChatMessage


class TokenCounter(ABC):
    """Contract for estimating the token cost of chat messages."""

    @abstractmethod
    def count(self, message: ChatMessage) -> int:
        """Return the estimated token count for a message."""
        raise NotImplementedError


class CharacterTokenCounter(TokenCounter):
    """Simple deterministic token estimator.

    This is intentionally approximate and is not model-specific.
    """

    def count(self, message: ChatMessage) -> int:
        if not message.content:
            return 0

        return max(1, (len(message.content) + 3) // 4)
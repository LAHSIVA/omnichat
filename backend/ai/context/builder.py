from ai.domain.types import ChatMessage
from ai.context.token_counter import TokenCounter
from ai.domain.exceptions import ContextLimitError


class ContextBuilder:
    """Builds a bounded conversation context."""

    def __init__(
        self,
        token_counter: TokenCounter,
        max_tokens: int,
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")

        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def build(
        self,
        messages: list[ChatMessage],
    ) -> list[ChatMessage]:
        if not messages:
            return []

        system_messages = [
            message
            for message in messages
            if message.role == "system"
        ]

        non_system_messages = [
            message
            for message in messages
            if message.role != "system"
        ]

        system_tokens = sum(
            self.token_counter.count(message)
            for message in system_messages
        )

        if system_tokens > self.max_tokens:
            raise ContextLimitError(
                "system message exceeds the context limit"
            )

        latest_message = non_system_messages[-1]

        latest_tokens = self.token_counter.count(
            latest_message
        )

        if system_tokens + latest_tokens > self.max_tokens:
            raise ContextLimitError(
                "latest message exceeds the context limit"
            )

        selected = list(system_messages)
        selected.append(latest_message)

        total_tokens = system_tokens + latest_tokens

        for message in reversed(non_system_messages[:-1]):
            message_tokens = self.token_counter.count(message)

            if total_tokens + message_tokens > self.max_tokens:
                continue

            selected.append(message)
            total_tokens += message_tokens

        system_count = len(system_messages)

        conversation_messages = selected[system_count:]
        conversation_messages.reverse()

        return selected[:system_count] + conversation_messages
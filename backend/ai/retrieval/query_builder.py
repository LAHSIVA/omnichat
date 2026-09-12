from ai.domain.types import ChatMessage


class RetrievalQueryBuilder:
    """Builds self-contained queries for document retrieval."""

    def build(
        self,
        *,
        content: str,
        history: list[ChatMessage],
    ) -> str:
        """Build a retrieval query from the current question and history."""

        if not history:
            return content

        recent_history = history[-6:]

        conversation_context = "\n".join(
            f"{message.role}: {message.content}"
            for message in recent_history
        )

        return (
            "Resolve any references or pronouns in the latest question "
            "using the conversation context. "
            "Return a self-contained search query.\n\n"
            f"Conversation:\n{conversation_context}\n\n"
            f"Latest question:\n{content}"
        )

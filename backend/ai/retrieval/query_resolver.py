from ai.domain.types import ChatMessage


class RetrievalQueryResolver:
    """Resolves conversational questions into self-contained retrieval queries."""

    PRONOUNS = {
        "he",
        "him",
        "his",
        "she",
        "her",
        "hers",
        "they",
        "them",
        "their",
        "it",
        "this",
        "that",
        "these",
        "those",
    }

    def resolve(
        self,
        *,
        query: str,
        history: list[ChatMessage],
    ) -> str:
        """Return a retrieval-friendly query using recent conversation context."""

        if not history:
            return query

        if not self._needs_resolution(query):
            return query

        context = self._build_recent_context(history)

        if not context:
            return query

        return (
            f"{context}\n"
            f"Current question: {query}"
        )

    def _needs_resolution(self, query: str) -> bool:
        """Determine whether a query likely depends on conversation context."""

        words = {
            word.strip(".,?!:;()[]{}\"'").lower()
            for word in query.split()
        }

        return bool(words & self.PRONOUNS)

    @staticmethod
    def _build_recent_context(
        history: list[ChatMessage],
        max_messages: int = 6,
    ) -> str:
        """Build a small recent conversation context for retrieval."""

        recent_messages = history[-max_messages:]

        return "\n".join(
            f"{message.role}: {message.content}"
            for message in recent_messages
            if message.content.strip()
        )

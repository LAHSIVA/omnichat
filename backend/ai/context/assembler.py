from ai.domain.types import ChatMessage, RetrievedChunk

class ContextAssembler:
    """Assembles conversation history and retrieved knowledge."""

    def assemble(
        self,
        *,
        history: list[ChatMessage],
        knowledge_chunks: list[RetrievedChunk],
    ) -> list[ChatMessage]:
        if not knowledge_chunks:
            return list(history)

        messages = [
            ChatMessage(
                role="system",
                content=(
                    "Use the following knowledge to answer the "
                    "user's question."
                ),
            ),
        ]

        messages.extend(
            ChatMessage(
                role="system",
                content=chunk.content,
                is_optional=True,
            )
            for chunk in knowledge_chunks
        )

        messages.extend(history)

        return messages
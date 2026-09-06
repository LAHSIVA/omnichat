from ai.domain.enums import ResponseMode
from ai.domain.types import ChatMessage, RetrievedChunk


class ContextAssembler:
    """Assembles conversation context for the selected response mode."""

    GENERAL_SYSTEM_PROMPT = (
        "You are OmniChat, a helpful AI assistant. "
        "Answer the user's question using your general knowledge "
        "and the conversation history."
    )

    RAG_SYSTEM_PROMPT = (
        "You are OmniChat, a document-grounded AI assistant. "
        "Answer the user's question using the conversation history "
        "and the information provided in the uploaded documents. "
        "Do not invent information that is not supported by the "
        "provided documents."
    )

    def assemble(
        self,
        *,
        history: list[ChatMessage],
        knowledge_chunks: list[RetrievedChunk],
        mode: ResponseMode,
    ) -> list[ChatMessage]:
        """Build messages for general chat or document-grounded chat."""

        if mode == ResponseMode.GENERAL:
            return [
                ChatMessage(
                    role="system",
                    content=self.GENERAL_SYSTEM_PROMPT,
                ),
                *history,
            ]

        if mode != ResponseMode.RAG:
            raise ValueError(f"Unsupported response mode: {mode}")

        messages = [
            ChatMessage(
                role="system",
                content=self.RAG_SYSTEM_PROMPT,
            )
        ]

        for chunk in knowledge_chunks:
            messages.append(
                ChatMessage(
                    role="system",
                    content=self._build_knowledge_context(chunk),
                    is_optional=True,
                )
            )

        messages.extend(history)

        return messages

    @staticmethod
    def _build_knowledge_context(
        chunk: RetrievedChunk,
    ) -> str:
        """Build a clearly delimited context block for one chunk."""

        return (
            "DOCUMENT CONTEXT\n\n"
            f"--- Source: {chunk.document_title} ---\n"
            f"{chunk.content}\n"
            "--- End Source ---"
        )

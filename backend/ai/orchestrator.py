from collections.abc import Iterator
from dataclasses import dataclass

from django.conf import settings

from ai.context.assembler import ContextAssembler
from ai.context.builder import ContextBuilder
from ai.context.token_counter import CharacterTokenCounter
from ai.domain.enums import ResponseMode
from ai.domain.types import ChatMessage, LLMResponse, RetrievedChunk
from ai.factory import create_llm_gateway
from ai.retrieval.relevance import RelevanceEvaluator
from ai.retrieval.service import RetrievalService
from conversations.models import Conversation, Message, MessageSource
from conversations.serializers import MessageSerializer
from knowledge.knowledge_search import KnowledgeSearchService


@dataclass(frozen=True)
class ChatResult:
    """Contains the result of a completed chat request."""

    user_message: Message
    assistant_message: Message
    llm_response: LLMResponse
    sources: list[RetrievedChunk]
    mode: ResponseMode


class ChatOrchestrator:
    """Coordinates conversational chat and document-grounded RAG."""

    def __init__(
        self,
        gateway=None,
        context_builder=None,
        context_assembler=None,
        knowledge_search=None,
        retrieval_service=None,
        model=None,
    ):
        self.gateway = gateway or create_llm_gateway(model=model)

        self.context_builder = (
            context_builder
            or ContextBuilder(
                token_counter=CharacterTokenCounter(),
                max_tokens=settings.AI_CONTEXT_MAX_TOKENS,
            )
        )

        self.context_assembler = (
            context_assembler or ContextAssembler()
        )

        if retrieval_service is not None:
            self.retrieval_service = retrieval_service
        else:
            if knowledge_search is None:
                knowledge_search = KnowledgeSearchService()

            relevance_evaluator = RelevanceEvaluator(
                max_distance=settings.KNOWLEDGE_SEARCH_MAX_DISTANCE,
            )

            self.retrieval_service = RetrievalService(
                knowledge_search=knowledge_search,
                relevance_evaluator=relevance_evaluator,
            )

    def _retrieve(
        self,
        *,
        content: str,
        conversation: Conversation,
    ):
        """Retrieve knowledge and determine the response mode."""

        return self.retrieval_service.retrieve(
            query=content,
            user=conversation.user,
            limit=settings.AI_KNOWLEDGE_TOP_K,
        )

    @staticmethod
    def _get_history(
        conversation: Conversation,
    ) -> list[ChatMessage]:
        """Return conversation history as domain messages."""

        history = conversation.messages.order_by("created_at")

        return [
            ChatMessage(
                role=message.role,
                content=message.content,
            )
            for message in history
        ]

    def _build_context(
        self,
        *,
        history: list[ChatMessage],
        chunks: list[RetrievedChunk],
        mode: ResponseMode,
    ) -> list[ChatMessage]:
        """Build and token-bound the LLM context."""

        messages = self.context_assembler.assemble(
            history=history,
            knowledge_chunks=chunks,
            mode=mode,
        )

        return self.context_builder.build(messages)

    @staticmethod
    def _save_sources(
        *,
        message: Message,
        sources: list[RetrievedChunk],
    ) -> None:
        """Persist document sources associated with an assistant message."""

        for source in sources:
            if not hasattr(source, "document_id"):
                continue

            MessageSource.objects.create(
                message=message,
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                distance=source.distance,
            )

    def chat(
        self,
        *,
        conversation: Conversation,
        content: str,
    ) -> ChatResult:
        """Generate a complete assistant response."""

        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=content,
        )

        retrieval = self._retrieve(
            content=content,
            conversation=conversation,
        )

        mode = (
            ResponseMode.RAG
            if retrieval.is_relevant
            else ResponseMode.GENERAL
        )

        history = self._get_history(conversation)

        bounded_messages = self._build_context(
            history=history,
            chunks=retrieval.chunks,
            mode=mode,
        )

        llm_response = self.gateway.generate(
            bounded_messages,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=llm_response.content,
        )

        if mode == ResponseMode.RAG:
            self._save_sources(
                message=assistant_message,
                sources=retrieval.chunks,
            )

        return ChatResult(
            user_message=user_message,
            assistant_message=assistant_message,
            llm_response=llm_response,
            sources=(
                retrieval.chunks
                if mode == ResponseMode.RAG
                else []
            ),
            mode=mode,
        )

    def chat_stream(
        self,
        *,
        conversation: Conversation,
        content: str,
    ) -> Iterator[dict]:
        """Generate an assistant response as a token stream."""

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=content,
        )

        yield {
            "type": "status",
            "stage": "preparing",
            "message": "Preparing your question...",
        }

        yield {
            "type": "status",
            "stage": "retrieving",
            "message": "Searching your uploaded documents...",
        }

        retrieval = self._retrieve(
            content=content,
            conversation=conversation,
        )

        mode = (
            ResponseMode.RAG
            if retrieval.is_relevant
            else ResponseMode.GENERAL
        )

        if mode == ResponseMode.RAG:
            yield {
                "type": "status",
                "stage": "retrieved",
                "message": (
                    f"Found {len(retrieval.chunks)} relevant "
                    "document sections."
                ),
            }
        else:
            yield {
                "type": "status",
                "stage": "general",
                "message": (
                    "No relevant information found in your "
                    "documents. Answering as a general question."
                ),
            }

        yield {
            "type": "status",
            "stage": "building_context",
            "message": "Building response context...",
        }

        history = self._get_history(conversation)

        bounded_messages = self._build_context(
            history=history,
            chunks=retrieval.chunks,
            mode=mode,
        )

        yield {
            "type": "status",
            "stage": "generating",
            "message": "Generating response...",
        }

        response_chunks: list[str] = []

        for chunk in self.gateway.generate_stream(
            bounded_messages,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        ):
            response_chunks.append(chunk)

            yield {
                "type": "token",
                "content": chunk,
            }

        full_content = "".join(response_chunks)

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=full_content,
        )

        sources = (
            retrieval.chunks
            if mode == ResponseMode.RAG
            else []
        )

        if mode == ResponseMode.RAG:
            self._save_sources(
                message=assistant_message,
                sources=sources,
            )

        yield {
            "type": "done",
            "message": MessageSerializer(assistant_message).data,
            "sources": sources,
            "mode": mode,
        }

from dataclasses import dataclass

from ai.context.builder import ContextBuilder
from ai.context.token_counter import CharacterTokenCounter
from ai.domain.types import ChatMessage, LLMResponse, RetrievedChunk
from ai.factory import create_llm_gateway
from conversations.models import Conversation, Message, MessageSource
from django.conf import settings
from knowledge.knowledge_search import KnowledgeSearchService
from ai.context.assembler import ContextAssembler
from collections.abc import Iterator
from conversations.serializers import MessageSerializer
@dataclass(frozen=True)
class ChatResult:
    user_message: Message
    assistant_message: Message
    llm_response: LLMResponse
    sources: list[RetrievedChunk]


class ChatOrchestrator:
    def __init__(
        self,
        gateway=None,
        context_builder=None,
        knowledge_search=None,
        context_assembler=None,
    ):
        self.context_assembler = (
        context_assembler
        or ContextAssembler()
    )
        self.gateway = gateway or create_llm_gateway()
        self.context_builder = (
            context_builder
            or ContextBuilder(
                token_counter=CharacterTokenCounter(),
                max_tokens=settings.AI_CONTEXT_MAX_TOKENS,
            )
        )
        self.knowledge_search = (
            knowledge_search
            or KnowledgeSearchService()
        )

    def chat(
        self,
        *,
        conversation: Conversation,
        content: str,
    ) -> ChatResult:

        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=content,
        )

        knowledge_chunks = self.knowledge_search.search(
            query=content,
            user=conversation.user,
            limit=settings.AI_KNOWLEDGE_TOP_K,
        )

        history = conversation.messages.order_by("created_at")

        history_messages = [
            ChatMessage(
                role=message.role,
                content=message.content,
            )
            for message in history
        ]

        chat_messages = self.context_assembler.assemble(
            history=history_messages,
            knowledge_chunks=knowledge_chunks,
        )

        bounded_messages = self.context_builder.build(
            chat_messages,
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
        for source in knowledge_chunks:
            if not hasattr(source, "document_id"):
                continue

            MessageSource.objects.create(
                message=assistant_message,
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                distance=source.distance,
            )

        return ChatResult(
            user_message=user_message,
            assistant_message=assistant_message,
            llm_response=llm_response,
            sources=knowledge_chunks,
        )

    def chat_stream(
        self,
        *,
        conversation: Conversation,
        content: str,
    ) -> Iterator[dict]:
        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=content,
        )

        knowledge_chunks = self.knowledge_search.search(
            query=content,
            user=conversation.user,
            limit=settings.AI_KNOWLEDGE_TOP_K,
        )

        history = conversation.messages.order_by("created_at")

        history_messages = [
            ChatMessage(
                role=message.role,
                content=message.content,
            )
            for message in history
        ]

        chat_messages = self.context_assembler.assemble(
            history=history_messages,
            knowledge_chunks=knowledge_chunks,
        )

        bounded_messages = self.context_builder.build(
            chat_messages,
        )

        chunks: list[str] = []

        for chunk in self.gateway.generate_stream(
            bounded_messages,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        ):
            chunks.append(chunk)
            yield {
                "type": "token",
                "content": chunk,
            }

        full_content = "".join(chunks)

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=full_content,
        )

        for source in knowledge_chunks:
            if not hasattr(source, "document_id"):
                continue

            MessageSource.objects.create(
                message=assistant_message,
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                distance=source.distance,
            )

        yield {
            "type": "done",
            "message": MessageSerializer(assistant_message).data,
            "sources": knowledge_chunks,
        }     
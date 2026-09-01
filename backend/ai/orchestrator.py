from dataclasses import dataclass

from ai.context.builder import ContextBuilder
from ai.context.token_counter import CharacterTokenCounter
from ai.domain.types import ChatMessage, LLMResponse
from ai.factory import create_llm_gateway
from conversations.models import Conversation, Message
from django.conf import settings

@dataclass(frozen=True)
class ChatResult:
    user_message: Message
    assistant_message: Message
    llm_response: LLMResponse


class ChatOrchestrator:
    def __init__(
        self,
        gateway=None,
        context_builder=None,
    ):
        self.gateway = gateway or create_llm_gateway()
        self.context_builder = (
            context_builder
            or ContextBuilder(
                token_counter=CharacterTokenCounter(),
                max_tokens=settings.AI_CONTEXT_MAX_TOKENS,
            )
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

        history = conversation.messages.order_by("created_at")

        chat_messages = [
            ChatMessage(
                role=message.role,
                content=message.content,
            )
            for message in history
        ]

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

        return ChatResult(
            user_message=user_message,
            assistant_message=assistant_message,
            llm_response=llm_response,
        )
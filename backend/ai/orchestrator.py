from dataclasses import dataclass

from ai.domain.types import ChatMessage, LLMResponse
from ai.factory import create_llm_gateway
from conversations.models import Conversation, Message


@dataclass(frozen=True)
class ChatResult:
    user_message: Message
    assistant_message: Message
    llm_response: LLMResponse


class ChatOrchestrator:
    def __init__(self, gateway=None):
        self.gateway = gateway or create_llm_gateway()

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

        llm_response = self.gateway.generate(
            chat_messages,
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
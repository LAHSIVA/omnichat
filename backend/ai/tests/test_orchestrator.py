import pytest

from ai.domain.types import LLMResponse
from ai.orchestrator import ChatOrchestrator
from conversations.models import Conversation, Message
from ai.domain.exceptions import LLMProviderError
from django.conf import settings
class FakeGateway:
    def __init__(self, response=None):
        self.response = response or LLMResponse(
            content="Fake assistant response",
            model="fake-model",
            provider="fake",
            usage=None,
            finish_reason="stop",
        )
        self.received_messages = None
        self.received_max_tokens = None

    def generate(
        self,
        messages,
        *,
        max_tokens=None,
    ):
        self.received_messages = messages
        self.received_max_tokens = max_tokens
        return self.response

class FailingGateway:
    def generate(
        self,
        messages,
        *,
        max_tokens=None,
    ):
        raise LLMProviderError("LLM provider failed")


@pytest.mark.django_db
def test_user_message_is_persisted(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="persistuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Test Conversation",
    )

    gateway = FakeGateway()
    orchestrator = ChatOrchestrator(gateway=gateway)

    result = orchestrator.chat(
        conversation=conversation,
        content="What is RAG?",
    )

    assert result.user_message.content == "What is RAG?"
    assert result.user_message.role == Message.Role.USER

    assert Message.objects.filter(
        conversation=conversation,
        role=Message.Role.USER,
        content="What is RAG?",
    ).exists()


@pytest.mark.django_db
def test_gateway_receives_conversation_history(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="historyuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="History Test",
    )

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content="Hello",
    )

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content="Hi! How can I help?",
    )

    gateway = FakeGateway()
    orchestrator = ChatOrchestrator(gateway=gateway)

    orchestrator.chat(
        conversation=conversation,
        content="Explain RAG",
    )

    assert len(gateway.received_messages) == 3

    assert gateway.received_messages[0].role == Message.Role.USER
    assert gateway.received_messages[0].content == "Hello"

    assert gateway.received_messages[1].role == Message.Role.ASSISTANT
    assert gateway.received_messages[1].content == "Hi! How can I help?"

    assert gateway.received_messages[2].role == Message.Role.USER
    assert gateway.received_messages[2].content == "Explain RAG"


@pytest.mark.django_db
def test_assistant_response_is_persisted(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="assistantuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Assistant Test",
    )

    gateway = FakeGateway()
    orchestrator = ChatOrchestrator(gateway=gateway)

    result = orchestrator.chat(
        conversation=conversation,
        content="What is machine learning?",
    )

    assistant_message = result.assistant_message

    assert assistant_message.role == Message.Role.ASSISTANT
    assert assistant_message.content == "Fake assistant response"

    assert Message.objects.filter(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content="Fake assistant response",
    ).exists()


@pytest.mark.django_db
def test_chat_returns_complete_chat_result(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="resultuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Result Test",
    )

    gateway = FakeGateway()
    orchestrator = ChatOrchestrator(gateway=gateway)

    result = orchestrator.chat(
        conversation=conversation,
        content="What is an embedding?",
    )

    assert result.user_message.content == "What is an embedding?"
    assert result.user_message.role == Message.Role.USER

    assert result.assistant_message.content == "Fake assistant response"
    assert result.assistant_message.role == Message.Role.ASSISTANT

    assert result.llm_response.content == "Fake assistant response"
    assert result.llm_response.provider == "fake"
    assert result.llm_response.model == "fake-model"


@pytest.mark.django_db
def test_user_message_is_preserved_when_llm_fails(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="failureuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Failure Test",
    )

    gateway = FailingGateway()
    orchestrator = ChatOrchestrator(gateway=gateway)

    with pytest.raises(LLMProviderError, match="LLM provider failed"):
        orchestrator.chat(
            conversation=conversation,
            content="This should survive an LLM failure",
        )

    assert Message.objects.filter(
        conversation=conversation,
        role=Message.Role.USER,
        content="This should survive an LLM failure",
    ).exists()

    assert not Message.objects.filter(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
    ).exists()

def test_orchestrator_uses_context_builder(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="contextuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Context Test",
    )

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content="Old message",
    )

    gateway = FakeGateway()

    class FakeContextBuilder:
        def __init__(self):
            self.received_messages = None

        def build(self, messages):
            self.received_messages = messages

            return messages[-1:]

    context_builder = FakeContextBuilder()

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        context_builder=context_builder,
    )

    orchestrator.chat(
        conversation=conversation,
        content="New message",
    )

    assert context_builder.received_messages is not None

    assert [
        message.content
        for message in context_builder.received_messages
    ] == [
        "Old message",
        "New message",
    ]

    assert len(gateway.received_messages) == 1
    assert gateway.received_messages[0].content == "New message"

@pytest.mark.django_db
def test_orchestrator_passes_configured_output_token_limit(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="outputlimituser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Output Limit Test",
    )

    gateway = FakeGateway()

    orchestrator = ChatOrchestrator(
        gateway=gateway,
    )

    orchestrator.chat(
        conversation=conversation,
        content="Explain RAG",
    )

    assert (
        gateway.received_max_tokens
        == settings.AI_MAX_OUTPUT_TOKENS
    )
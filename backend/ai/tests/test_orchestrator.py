import pytest

from ai.domain.types import LLMResponse
from ai.orchestrator import ChatOrchestrator
from conversations.models import Conversation, Message
from ai.domain.exceptions import LLMProviderError
from django.conf import settings
from ai.domain.exceptions import ContextLimitError
from ai.context.builder import ContextBuilder
from ai.context.token_counter import CharacterTokenCounter

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

@pytest.mark.django_db
def test_orchestrator_includes_retrieved_knowledge_in_context(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="raguser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="RAG Test",
    )

    class FakeKnowledgeChunk:
        def __init__(self, content):
            self.content = content

    class FakeKnowledgeSearch:
        def __init__(self):
            self.received_query = None
            self.received_user = None

        def search(
            self,
            query,
            user,
            limit=5,
        ):
            self.received_query = query
            self.received_user = user

            return [
                FakeKnowledgeChunk(
                    "Predictive maintenance uses machine learning "
                    "to detect equipment failures."
                ),
                FakeKnowledgeChunk(
                    "Sensors can monitor equipment health "
                    "and identify abnormal behavior."
                ),
            ]

    gateway = FakeGateway()
    knowledge_search = FakeKnowledgeSearch()

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        knowledge_search=knowledge_search,
    )

    orchestrator.chat(
        conversation=conversation,
        content="How does predictive maintenance work?",
    )

    assert knowledge_search.received_query == (
        "How does predictive maintenance work?"
    )

    assert knowledge_search.received_user == user

    gateway_contents = [
        message.content
        for message in gateway.received_messages
    ]

    assert any(
        "Predictive maintenance uses machine learning"
        in content
        for content in gateway_contents
    )

    assert any(
        "Sensors can monitor equipment health"
        in content
        for content in gateway_contents
    )

@pytest.mark.django_db
def test_orchestrator_handles_no_retrieved_knowledge(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="noraguser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="No RAG Test",
    )

    class EmptyKnowledgeSearch:
        def search(
            self,
            query,
            user,
            limit=5,
        ):
            return []

    gateway = FakeGateway()

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        knowledge_search=EmptyKnowledgeSearch(),
    )

    orchestrator.chat(
        conversation=conversation,
        content="What is machine learning?",
    )

    assert len(gateway.received_messages) == 1

    assert gateway.received_messages[0].role == Message.Role.USER

    assert (
        gateway.received_messages[0].content
        == "What is machine learning?"
    )

@pytest.mark.django_db
def test_orchestrator_skips_knowledge_that_exceeds_context_limit(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="oversizedraguser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Oversized RAG Test",
    )

    class LargeKnowledgeChunk:
        def __init__(self):
            self.content = "x" * 100000

    class LargeKnowledgeSearch:
        def search(
            self,
            query,
            user,
            limit=5,
        ):
            return [LargeKnowledgeChunk()]

    gateway = FakeGateway()

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        knowledge_search=LargeKnowledgeSearch(),
    )

    result = orchestrator.chat(
        conversation=conversation,
        content="What is predictive maintenance?",
    )

    assert result.assistant_message.content == (
        "Fake assistant response"
    )

    assert len(gateway.received_messages) == 2

    assert gateway.received_messages[0].role == "system"
    assert gateway.received_messages[0].is_optional is False

    assert gateway.received_messages[1].role == "user"
    assert gateway.received_messages[1].content == (
        "What is predictive maintenance?"
    )

    assert Message.objects.filter(
        conversation=conversation,
        role=Message.Role.USER,
        content="What is predictive maintenance?",
    ).exists()

    assert Message.objects.filter(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content="Fake assistant response",
    ).exists()


@pytest.mark.django_db
def test_orchestrator_limits_retrieved_knowledge_to_context_budget(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="ragbudgetuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="RAG Budget Test",
    )

    class FakeKnowledgeChunk:
        def __init__(self, content):
            self.content = content

    class FakeKnowledgeSearch:
        def search(
            self,
            query,
            user,
            limit=5,
        ):
            return [
                FakeKnowledgeChunk("A" * 20),
                FakeKnowledgeChunk("B" * 80),
            ]

    gateway = FakeGateway()

    context_builder = ContextBuilder(
        token_counter=CharacterTokenCounter(),
        max_tokens=30,
    )

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        context_builder=context_builder,
        knowledge_search=FakeKnowledgeSearch(),
    )

    orchestrator.chat(
        conversation=conversation,
        content="What is predictive maintenance?",
    )

    assert any(
        message.content == "A" * 20
        for message in gateway.received_messages
    )

    assert not any(
        message.content == "B" * 80
        for message in gateway.received_messages
    )

    assert any(
        message.content == "What is predictive maintenance?"
        for message in gateway.received_messages
    )
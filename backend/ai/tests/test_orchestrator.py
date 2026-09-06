import pytest

from ai.context.builder import ContextBuilder
from ai.context.token_counter import CharacterTokenCounter
from ai.domain.enums import ResponseMode
from ai.domain.exceptions import LLMProviderError
from ai.domain.retrieval import RetrievalResult
from ai.domain.types import LLMResponse, RetrievedChunk
from ai.orchestrator import ChatOrchestrator
from conversations.models import Conversation, Message, MessageSource
from knowledge.models import Document, DocumentChunk


class FakeGateway:
    """Fake LLM gateway for orchestrator tests."""

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

    def generate(self, messages, *, max_tokens=None):
        """Return a deterministic response."""
        self.received_messages = messages
        self.received_max_tokens = max_tokens
        return self.response

    def generate_stream(self, messages, *, max_tokens=None):
        """Return a deterministic streaming response."""
        self.received_messages = messages
        self.received_max_tokens = max_tokens

        yield "Fake "
        yield "streaming "
        yield "response"


class FailingGateway:
    """Fake gateway that raises an LLM error."""

    def generate(self, messages, *, max_tokens=None):
        """Raise an LLM provider error."""
        raise LLMProviderError("LLM provider failed")


class FakeRetrievalService:
    """Fake retrieval service for deterministic tests."""

    def __init__(self, chunks=None, is_relevant=False):
        self.chunks = chunks or []
        self.is_relevant = is_relevant
        self.received_query = None
        self.received_user = None
        self.received_limit = None

    def retrieve(self, *, query, user, limit):
        """Return a deterministic retrieval result."""
        self.received_query = query
        self.received_user = user
        self.received_limit = limit

        return RetrievalResult(
            chunks=self.chunks,
            is_relevant=self.is_relevant,
        )


def make_chunk(
    *,
    content="Predictive maintenance content.",
    document_id=1,
    document_title="Predictive Maintenance",
    original_filename="predictive_maintenance.txt",
    chunk_id=1,
    chunk_index=0,
    distance=0.10,
):
    """Create a deterministic retrieved chunk."""
    return RetrievedChunk(
        content=content,
        document_id=document_id,
        document_title=document_title,
        original_filename=original_filename,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        distance=distance,
    )


@pytest.fixture
def empty_retrieval_service():
    """Provide a retrieval service with no relevant knowledge."""
    return FakeRetrievalService(
        chunks=[],
        is_relevant=False,
    )


@pytest.fixture
def relevant_retrieval_service(django_user_model):
    """Provide relevant database-backed retrieval results."""

    user = django_user_model.objects.create_user(
        username="retrieval-fixture-user",
        password="test-password",
    )

    document = Document.objects.create(
        user=user,
        title="Predictive Maintenance",
        original_filename="predictive_maintenance.txt",
        content_type="text/plain",
    )

    first_chunk = DocumentChunk.objects.create(
        document=document,
        content=(
            "Predictive maintenance uses machine learning "
            "to detect equipment failures."
        ),
        chunk_index=0,
    )

    second_chunk = DocumentChunk.objects.create(
        document=document,
        content=(
            "Sensors can monitor equipment health "
            "and identify abnormal behavior."
        ),
        chunk_index=1,
    )

    return FakeRetrievalService(
        chunks=[
            make_chunk(
                content=first_chunk.content,
                document_id=document.id,
                document_title=document.title,
                original_filename=document.original_filename,
                chunk_id=first_chunk.id,
                chunk_index=first_chunk.chunk_index,
                distance=0.10,
            ),
            make_chunk(
                content=second_chunk.content,
                document_id=document.id,
                document_title=document.title,
                original_filename=document.original_filename,
                chunk_id=second_chunk.id,
                chunk_index=second_chunk.chunk_index,
                distance=0.20,
            ),
        ],
        is_relevant=True,
    )


@pytest.mark.django_db
def test_user_message_is_persisted(
    django_user_model,
    empty_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="persistuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Test Conversation",
    )

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=empty_retrieval_service,
    )

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
    empty_retrieval_service,
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

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        retrieval_service=empty_retrieval_service,
    )

    orchestrator.chat(
        conversation=conversation,
        content="Explain RAG",
    )

    assert gateway.received_messages[0].role == "system"

    assert gateway.received_messages[1].role == Message.Role.USER
    assert gateway.received_messages[1].content == "Hello"

    assert gateway.received_messages[2].role == Message.Role.ASSISTANT
    assert gateway.received_messages[2].content == (
        "Hi! How can I help?"
    )

    assert gateway.received_messages[3].role == Message.Role.USER
    assert gateway.received_messages[3].content == "Explain RAG"


@pytest.mark.django_db
def test_assistant_response_is_persisted(
    django_user_model,
    empty_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="assistantuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Assistant Test",
    )

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=empty_retrieval_service,
    )

    result = orchestrator.chat(
        conversation=conversation,
        content="What is machine learning?",
    )

    assert result.assistant_message.role == Message.Role.ASSISTANT
    assert result.assistant_message.content == (
        "Fake assistant response"
    )

    assert Message.objects.filter(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content="Fake assistant response",
    ).exists()


@pytest.mark.django_db
def test_chat_returns_general_result(
    django_user_model,
    empty_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="resultuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Result Test",
    )

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=empty_retrieval_service,
    )

    result = orchestrator.chat(
        conversation=conversation,
        content="What is an embedding?",
    )

    assert result.user_message.content == "What is an embedding?"

    assert result.assistant_message.content == (
        "Fake assistant response"
    )

    assert result.llm_response.content == (
        "Fake assistant response"
    )

    assert result.llm_response.provider == "fake"
    assert result.llm_response.model == "fake-model"

    assert result.mode == ResponseMode.GENERAL
    assert result.sources == []


@pytest.mark.django_db
def test_user_message_is_preserved_when_llm_fails(
    django_user_model,
    empty_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="failureuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Failure Test",
    )

    orchestrator = ChatOrchestrator(
        gateway=FailingGateway(),
        retrieval_service=empty_retrieval_service,
    )

    with pytest.raises(
        LLMProviderError,
        match="LLM provider failed",
    ):
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


@pytest.mark.django_db
def test_orchestrator_uses_context_builder(
    django_user_model,
    empty_retrieval_service,
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
        retrieval_service=empty_retrieval_service,
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
        "You are OmniChat, a helpful AI assistant. "
        "Answer the user's question using your general knowledge "
        "and the conversation history.",
        "Old message",
        "New message",
    ]

    assert len(gateway.received_messages) == 1
    assert gateway.received_messages[0].content == "New message"


@pytest.mark.django_db
def test_orchestrator_passes_output_token_limit(
    django_user_model,
    empty_retrieval_service,
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
        retrieval_service=empty_retrieval_service,
    )

    orchestrator.chat(
        conversation=conversation,
        content="Explain RAG",
    )

    assert gateway.received_max_tokens == (
        __import__("django.conf").conf.settings.AI_MAX_OUTPUT_TOKENS
    )


@pytest.mark.django_db
def test_relevant_knowledge_uses_rag_mode(
    django_user_model,
    relevant_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="raguser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="RAG Test",
    )

    gateway = FakeGateway()

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        retrieval_service=relevant_retrieval_service,
    )

    result = orchestrator.chat(
        conversation=conversation,
        content="How does predictive maintenance work?",
    )

    assert result.mode == ResponseMode.RAG
    assert len(result.sources) == 2

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
def test_retrieval_service_receives_query_user_and_limit(
    django_user_model,
    empty_retrieval_service,
    settings,
):
    user = django_user_model.objects.create_user(
        username="retrievaluser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Retrieval Test",
    )

    settings.AI_KNOWLEDGE_TOP_K = 2

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=empty_retrieval_service,
    )

    orchestrator.chat(
        conversation=conversation,
        content="How does predictive maintenance work?",
    )

    assert empty_retrieval_service.received_query == (
        "How does predictive maintenance work?"
    )

    assert empty_retrieval_service.received_user == user
    assert empty_retrieval_service.received_limit == 2


@pytest.mark.django_db
def test_irrelevant_knowledge_uses_general_mode(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="generaluser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="General Test",
    )

    irrelevant_chunk = make_chunk(
        content="Completely unrelated document content.",
        distance=0.90,
    )

    retrieval_service = FakeRetrievalService(
        chunks=[irrelevant_chunk],
        is_relevant=False,
    )

    gateway = FakeGateway()

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        retrieval_service=retrieval_service,
    )

    result = orchestrator.chat(
        conversation=conversation,
        content="What is machine learning?",
    )

    assert result.mode == ResponseMode.GENERAL
    assert result.sources == []

    assert not any(
        "Completely unrelated document content."
        in message.content
        for message in gateway.received_messages
    )


@pytest.mark.django_db
def test_general_mode_does_not_persist_sources(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="nosourcesuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="No Sources Test",
    )

    document = Document.objects.create(
        user=user,
        title="Unrelated Document",
        original_filename="unrelated.txt",
        content_type="text/plain",
    )

    chunk = DocumentChunk.objects.create(
        document=document,
        content="Unrelated content.",
        chunk_index=0,
        embedding=[1.0] + [0.0] * 1023,
    )

    retrieved_chunk = make_chunk(
        content=chunk.content,
        document_id=document.id,
        document_title=document.title,
        original_filename=document.original_filename,
        chunk_id=chunk.id,
        distance=0.90,
    )

    retrieval_service = FakeRetrievalService(
        chunks=[retrieved_chunk],
        is_relevant=False,
    )

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=retrieval_service,
    )

    result = orchestrator.chat(
        conversation=conversation,
        content="Who won the World Cup?",
    )

    assert result.mode == ResponseMode.GENERAL
    assert result.sources == []

    assert not MessageSource.objects.filter(
        message=result.assistant_message,
    ).exists()


@pytest.mark.django_db
def test_rag_sources_are_persisted(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="persistedsourceuser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Persisted Sources Test",
    )

    document = Document.objects.create(
        user=user,
        title="Predictive Maintenance",
        original_filename="predictive_maintenance.txt",
        content_type="text/plain",
    )

    chunk = DocumentChunk.objects.create(
        document=document,
        content="Predictive maintenance content.",
        chunk_index=0,
        embedding=[1.0] + [0.0] * 1023,
    )

    retrieved_chunk = make_chunk(
        content=chunk.content,
        document_id=document.id,
        document_title=document.title,
        original_filename=document.original_filename,
        chunk_id=chunk.id,
        distance=0.12,
    )

    retrieval_service = FakeRetrievalService(
        chunks=[retrieved_chunk],
        is_relevant=True,
    )

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=retrieval_service,
    )

    result = orchestrator.chat(
        conversation=conversation,
        content="What is predictive maintenance?",
    )

    assert result.mode == ResponseMode.RAG
    assert len(result.sources) == 1

    source = MessageSource.objects.get(
        message=result.assistant_message,
    )

    assert source.document_id == document.id
    assert source.chunk_id == chunk.id
    assert source.distance == 0.12


@pytest.mark.django_db
def test_rag_context_is_bounded(
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

    document = Document.objects.create(
        user=user,
        title="RAG Budget Document",
        original_filename="rag_budget.txt",
        content_type="text/plain",
    )

    first_db_chunk = DocumentChunk.objects.create(
        document=document,
        content="A" * 20,
        chunk_index=0,
    )

    second_db_chunk = DocumentChunk.objects.create(
        document=document,
        content="B" * 80,
        chunk_index=1,
    )

    first_chunk = make_chunk(
        content=first_db_chunk.content,
        document_id=document.id,
        document_title=document.title,
        original_filename=document.original_filename,
        chunk_id=first_db_chunk.id,
        chunk_index=first_db_chunk.chunk_index,
        distance=0.10,
    )

    second_chunk = make_chunk(
        content=second_db_chunk.content,
        document_id=document.id,
        document_title=document.title,
        original_filename=document.original_filename,
        chunk_id=second_db_chunk.id,
        chunk_index=second_db_chunk.chunk_index,
        distance=0.20,
    )

    retrieval_service = FakeRetrievalService(
        chunks=[first_chunk, second_chunk],
        is_relevant=True,
    )

    gateway = FakeGateway()

    context_builder = ContextBuilder(
        token_counter=CharacterTokenCounter(),
        max_tokens=120,
    )

    orchestrator = ChatOrchestrator(
        gateway=gateway,
        context_builder=context_builder,
        retrieval_service=retrieval_service,
    )

    orchestrator.chat(
        conversation=conversation,
        content="What is predictive maintenance?",
    )

    assert any(
        "A" * 20 in message.content
        for message in gateway.received_messages
    )

    assert not any(
        "B" * 80 in message.content
        for message in gateway.received_messages
    )


@pytest.mark.django_db
def test_context_assembler_receives_general_mode(
    django_user_model,
    empty_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="assembleruser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Assembler Test",
    )

    class FakeContextAssembler:
        def __init__(self):
            self.received_mode = None
            self.received_knowledge = None

        def assemble(
            self,
            *,
            history,
            knowledge_chunks,
            mode,
        ):
            self.received_mode = mode
            self.received_knowledge = knowledge_chunks
            return history

    assembler = FakeContextAssembler()

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=empty_retrieval_service,
        context_assembler=assembler,
    )

    orchestrator.chat(
        conversation=conversation,
        content="New message",
    )

    assert assembler.received_mode == ResponseMode.GENERAL
    assert assembler.received_knowledge == []


@pytest.mark.django_db
def test_context_assembler_receives_rag_mode(
    django_user_model,
    relevant_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="ragassembleruser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="RAG Assembler Test",
    )

    class FakeContextAssembler:
        def __init__(self):
            self.received_mode = None
            self.received_knowledge = None

        def assemble(
            self,
            *,
            history,
            knowledge_chunks,
            mode,
        ):
            self.received_mode = mode
            self.received_knowledge = knowledge_chunks
            return history

    assembler = FakeContextAssembler()

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=relevant_retrieval_service,
        context_assembler=assembler,
    )

    orchestrator.chat(
        conversation=conversation,
        content="How does predictive maintenance work?",
    )

    assert assembler.received_mode == ResponseMode.RAG
    assert len(assembler.received_knowledge) == 2


@pytest.mark.django_db
def test_chat_stream_general_mode(
    django_user_model,
    empty_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="streamgeneraluser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Stream General Test",
    )

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=empty_retrieval_service,
    )

    events = list(
        orchestrator.chat_stream(
            conversation=conversation,
            content="What is machine learning?",
        )
    )

    event_types = [
        event["type"]
        for event in events
    ]

    assert event_types == [
        "status",
        "status",
        "status",
        "status",
        "status",
        "token",
        "token",
        "token",
        "done",
    ]

    status_events = [
        event
        for event in events
        if event["type"] == "status"
    ]

    assert [
        event["stage"]
        for event in status_events
    ] == [
        "preparing",
        "retrieving",
        "general",
        "building_context",
        "generating",
    ]

    assert [
        event["message"]
        for event in status_events
    ] == [
        "Preparing your question...",
        "Searching your uploaded documents...",
        (
            "No relevant information found in your "
            "documents. Answering as a general question."
        ),
        "Building response context...",
        "Generating response...",
    ]

    token_events = [
        event
        for event in events
        if event["type"] == "token"
    ]

    assert [
        event["content"]
        for event in token_events
    ] == [
        "Fake ",
        "streaming ",
        "response",
    ]

    assert events[-1]["mode"] == ResponseMode.GENERAL
    assert events[-1]["sources"] == []

    assistant = Message.objects.get(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
    )

    assert assistant.content == "Fake streaming response"


@pytest.mark.django_db
def test_chat_stream_rag_mode(
    django_user_model,
    relevant_retrieval_service,
):
    user = django_user_model.objects.create_user(
        username="streamraguser",
        password="test-password-123",
    )

    conversation = Conversation.objects.create(
        user=user,
        title="Stream RAG Test",
    )

    orchestrator = ChatOrchestrator(
        gateway=FakeGateway(),
        retrieval_service=relevant_retrieval_service,
    )

    events = list(
        orchestrator.chat_stream(
            conversation=conversation,
            content="How does predictive maintenance work?",
        )
    )

    event_types = [
        event["type"]
        for event in events
    ]

    assert event_types == [
        "status",
        "status",
        "status",
        "status",
        "status",
        "token",
        "token",
        "token",
        "done",
    ]

    status_events = [
        event
        for event in events
        if event["type"] == "status"
    ]

    assert [
        event["stage"]
        for event in status_events
    ] == [
        "preparing",
        "retrieving",
        "retrieved",
        "building_context",
        "generating",
    ]

    assert status_events[2]["message"] == (
        "Found 2 relevant document sections."
    )

    token_events = [
        event
        for event in events
        if event["type"] == "token"
    ]

    assert [
        event["content"]
        for event in token_events
    ] == [
        "Fake ",
        "streaming ",
        "response",
    ]

    assert events[-1]["type"] == "done"
    assert events[-1]["mode"] == ResponseMode.RAG
    assert len(events[-1]["sources"]) == 2

    assistant = Message.objects.get(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
    )

    assert assistant.content == "Fake streaming response"

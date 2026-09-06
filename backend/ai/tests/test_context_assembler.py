from ai.context.assembler import ContextAssembler
from ai.domain.enums import ResponseMode
from ai.domain.types import ChatMessage


class FakeChunk:
    """Simple retrieved chunk for assembler tests."""

    def __init__(self, content, document_title):
        self.content = content
        self.document_title = document_title


def test_context_assembler_builds_rag_context():
    assembler = ContextAssembler()

    history = [
        ChatMessage(
            role="user",
            content="Hello",
        ),
        ChatMessage(
            role="assistant",
            content="Hi!",
        ),
    ]

    knowledge_chunks = [
        FakeChunk(
            "Predictive maintenance detects equipment failures.",
            "maintenance.txt",
        ),
        FakeChunk(
            "Sensors monitor equipment health.",
            "sensors.txt",
        ),
    ]

    result = assembler.assemble(
        history=history,
        knowledge_chunks=knowledge_chunks,
        mode=ResponseMode.RAG,
    )

    # RAG system prompt.
    assert result[0].role == "system"
    assert "document-grounded" in result[0].content
    assert "uploaded documents" in result[0].content

    # Each retrieved chunk must be an independent optional
    # context message so ContextBuilder can remove lower-ranked
    # chunks when the token budget is reached.
    context_messages = [
        message
        for message in result
        if message.role == "system" and message.is_optional
    ]

    assert len(context_messages) == 2

    first_context = context_messages[0]
    second_context = context_messages[1]

    assert "DOCUMENT CONTEXT" in first_context.content
    assert "maintenance.txt" in first_context.content
    assert (
        "Predictive maintenance detects equipment failures."
        in first_context.content
    )

    assert "DOCUMENT CONTEXT" in second_context.content
    assert "sensors.txt" in second_context.content
    assert "Sensors monitor equipment health." in second_context.content

    # Conversation history remains after the document context.
    assert result[-2].role == "user"
    assert result[-2].content == "Hello"

    assert result[-1].role == "assistant"
    assert result[-1].content == "Hi!"


def test_context_assembler_builds_general_context():
    assembler = ContextAssembler()

    history = [
        ChatMessage(
            role="user",
            content="Hello",
        ),
        ChatMessage(
            role="assistant",
            content="Hi!",
        ),
    ]

    knowledge_chunks = [
        FakeChunk(
            "Private document information.",
            "private.txt",
        ),
    ]

    result = assembler.assemble(
        history=history,
        knowledge_chunks=knowledge_chunks,
        mode=ResponseMode.GENERAL,
    )

    assert result[0].role == "system"
    assert "helpful AI assistant" in result[0].content

    assert not any(
        "Private document information." in message.content
        for message in result
    )

    assert not any(
        "private.txt" in message.content
        for message in result
    )

    assert result[-2].role == "user"
    assert result[-2].content == "Hello"

    assert result[-1].role == "assistant"
    assert result[-1].content == "Hi!"


def test_context_assembler_general_mode_excludes_knowledge():
    assembler = ContextAssembler()

    knowledge_chunks = [
        FakeChunk(
            "Sensitive document content.",
            "secret.txt",
        ),
    ]

    result = assembler.assemble(
        history=[],
        knowledge_chunks=knowledge_chunks,
        mode=ResponseMode.GENERAL,
    )

    assert len(result) == 1
    assert result[0].role == "system"
    assert result[0].is_optional is False

    assert "Sensitive document content." not in result[0].content
    assert "secret.txt" not in result[0].content


def test_context_assembler_preserves_history_order():
    assembler = ContextAssembler()

    history = [
        ChatMessage(
            role="user",
            content="First question",
        ),
        ChatMessage(
            role="assistant",
            content="First answer",
        ),
        ChatMessage(
            role="user",
            content="Second question",
        ),
    ]

    result = assembler.assemble(
        history=history,
        knowledge_chunks=[],
        mode=ResponseMode.GENERAL,
    )

    assert [message.content for message in result] == [
        assembler.GENERAL_SYSTEM_PROMPT,
        "First question",
        "First answer",
        "Second question",
    ]

from ai.context.assembler import ContextAssembler
from ai.domain.types import ChatMessage


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

    class FakeChunk:
        def __init__(self, content):
            self.content = content

    knowledge_chunks=[
        FakeChunk(
            "Predictive maintenance detects equipment failures."
        ),
        FakeChunk(
            "Sensors monitor equipment health."
        ),
    ]

    result = assembler.assemble(
        history=history,
        knowledge_chunks=knowledge_chunks,
    )

    assert result[0].role == "system"
    assert (
        result[0].content
        == "Use the following knowledge to answer the user's question."
    )

    assert result[1].role == "system"
    assert result[1].content == (
        "Predictive maintenance detects equipment failures."
    )
    assert result[1].is_optional is True

    assert result[2].role == "system"
    assert result[2].content == (
        "Sensors monitor equipment health."
    )
    assert result[2].is_optional is True

    assert result[3] == history[0]
    assert result[4] == history[1]


def test_context_assembler_handles_no_knowledge():
    assembler = ContextAssembler()

    history = [
        ChatMessage(
            role="user",
            content="Hello",
        ),
    ]

    result = assembler.assemble(
        history=history,
        knowledge_chunks=[],
    )

    assert result == history


def test_context_assembler_preserves_history_order():
    class FakeChunk:
        def __init__(self, content):
            self.content = content

    assembler = ContextAssembler()

    history = [
        ChatMessage(role="user", content="First"),
        ChatMessage(role="assistant", content="Second"),
        ChatMessage(role="user", content="Third"),
    ]

    result = assembler.assemble(
        history=history,
        knowledge_chunks=[
            FakeChunk("Relevant knowledge")
        ],
    )

    assert [message.content for message in result if message.role != "system"] == [
    "First",
    "Second",
    "Third",
    ]
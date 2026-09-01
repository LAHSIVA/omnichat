import pytest

from ai.context.builder import ContextBuilder
from ai.context.token_counter import CharacterTokenCounter
from ai.domain.exceptions import ContextLimitError
from ai.domain.types import ChatMessage
def test_context_builder_keeps_messages_within_budget():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=10,
    )

    messages = [
        ChatMessage(
            role="user",
            content="12345678",  # 2 tokens
        ),
        ChatMessage(
            role="assistant",
            content="12345678",  # 2 tokens
        ),
        ChatMessage(
            role="user",
            content="12345678",  # 2 tokens
        ),
        ChatMessage(
            role="assistant",
            content="12345678",  # 2 tokens
        ),
        ChatMessage(
            role="user",
            content="12345678",  # 2 tokens
        ),
        ChatMessage(
            role="assistant",
            content="12345678",  # 2 tokens
        ),
    ]

    result = builder.build(messages)

    assert len(result) == 5
    assert result == messages[-5:]

def test_context_builder_preserves_chronological_order():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=8,
    )

    messages = [
        ChatMessage(role="user", content="11111111"),
        ChatMessage(role="assistant", content="22222222"),
        ChatMessage(role="user", content="33333333"),
        ChatMessage(role="assistant", content="44444444"),
        ChatMessage(role="user", content="55555555"),
    ]

    result = builder.build(messages)

    assert [message.content for message in result] == [
        "22222222",
        "33333333",
        "44444444",
        "55555555",
    ]

def test_context_builder_handles_empty_messages():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=100,
    )

    assert builder.build([]) == []

def test_context_builder_skips_message_that_exceeds_budget():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=10,
    )

    messages = [
        ChatMessage(
            role="user",
            content="12345678",  # 2 tokens
        ),
        ChatMessage(
            role="assistant",
            content="1" * 80,  # 20 tokens
        ),
        ChatMessage(
            role="user",
            content="12345678",  # 2 tokens
        ),
    ]

    result = builder.build(messages)

    assert result == [
        messages[0],
        messages[2],
    ]

def test_context_builder_rejects_zero_token_budget():
    counter = CharacterTokenCounter()

    with pytest.raises(
        ValueError,
        match="max_tokens must be greater than zero",
    ):
        ContextBuilder(
            token_counter=counter,
            max_tokens=0,
        )

def test_context_builder_rejects_negative_token_budget():
    counter = CharacterTokenCounter()

    with pytest.raises(
        ValueError,
        match="max_tokens must be greater than zero",
    ):
        ContextBuilder(
            token_counter=counter,
            max_tokens=-100,
        )

def test_context_builder_rejects_oversized_latest_message():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=10,
    )

    messages = [
        ChatMessage(
            role="user",
            content="Old message",
        ),
        ChatMessage(
            role="user",
            content="1" * 80,
        ),
    ]

    with pytest.raises(
        ContextLimitError,
        match="latest message exceeds the context limit",
    ):
        builder.build(messages)

def test_context_builder_always_preserves_system_message():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=10,
    )

    messages = [
        ChatMessage(
            role="system",
            content="System instruction",
        ),
        ChatMessage(
            role="user",
            content="Old message",
        ),
        ChatMessage(
            role="assistant",
            content="Old response",
        ),
        ChatMessage(
            role="user",
            content="Latest message",
        ),
    ]

    result = builder.build(messages)

    assert result[0].role == "system"
    assert result[0].content == "System instruction"

    assert result[-1].content == "Latest message"

def test_context_builder_preserves_multiple_system_messages():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=20,
    )

    messages = [
        ChatMessage(
            role="system",
            content="System one",
        ),
        ChatMessage(
            role="system",
            content="System two",
        ),
        ChatMessage(
            role="user",
            content="Hello",
        ),
    ]

    result = builder.build(messages)

    assert result == messages

def test_context_builder_can_skip_oversized_system_message():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=10,
    )

    messages = [
        ChatMessage(
            role="system",
            content="x" * 80,  # 20 tokens
            is_optional=True,
        ),
        ChatMessage(
            role="user",
            content="Hello",
        ),
    ]

    result = builder.build(messages)

    assert result == [
        messages[1],
    ]

def test_context_builder_skips_oversized_optional_system_message_but_keeps_fitting_context():
    counter = CharacterTokenCounter()

    builder = ContextBuilder(
        token_counter=counter,
        max_tokens=10,
    )

    messages = [
        ChatMessage(
            role="system",
            content="small",  # 2 tokens
            is_optional=True,
        ),
        ChatMessage(
            role="system",
            content="x" * 80,  # 20 tokens — skip
            is_optional=True,
        ),
        ChatMessage(
            role="user",
            content="Hello",  # 2 tokens
        ),
    ]

    result = builder.build(messages)

    assert result == [
        messages[0],
        messages[2],
    ]
from ai.context.token_counter import CharacterTokenCounter
from ai.domain.types import ChatMessage


def test_character_token_counter_estimates_tokens():
    counter = CharacterTokenCounter()

    message = ChatMessage(
        role="user",
        content="12345678",
    )

    assert counter.count(message) == 2

def test_character_token_counter_never_returns_zero_for_non_empty_content():
    counter = CharacterTokenCounter()

    message = ChatMessage(
        role="user",
        content="Hi",
    )

    assert counter.count(message) == 1

def test_character_token_counter_returns_zero_for_empty_content():
    counter = CharacterTokenCounter()

    message = ChatMessage(
        role="user",
        content="",
    )

    assert counter.count(message) == 0
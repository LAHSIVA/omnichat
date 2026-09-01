import pytest

from knowledge.chunking import TextChunker


def test_chunker_returns_empty_list_for_empty_text():
    chunker = TextChunker()

    assert chunker.chunk("") == []


def test_chunker_returns_empty_list_for_whitespace():
    chunker = TextChunker()

    assert chunker.chunk("   \n\t  ") == []


def test_chunker_keeps_short_text_as_one_chunk():
    chunker = TextChunker(
        max_characters=100,
        overlap_characters=10,
    )

    text = "This is a short document."

    assert chunker.chunk(text) == [text]


def test_chunker_splits_long_text():
    chunker = TextChunker(
        max_characters=20,
        overlap_characters=5,
    )

    text = (
        "This is a long document "
        "that needs to be split into "
        "multiple chunks."
    )

    chunks = chunker.chunk(text)

    assert len(chunks) > 1

    assert all(
        len(chunk) <= 20
        for chunk in chunks
    )


def test_chunker_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        TextChunker(max_characters=0)

    with pytest.raises(ValueError):
        TextChunker(
            max_characters=100,
            overlap_characters=-1,
        )

    with pytest.raises(ValueError):
        TextChunker(
            max_characters=100,
            overlap_characters=100,
        )

def test_chunker_preserves_overlap_between_chunks():
    chunker = TextChunker(
        max_characters=30,
        overlap_characters=10,
    )

    text = (
        "one two three four five six "
        "seven eight nine ten eleven twelve"
    )

    chunks = chunker.chunk(text)

    assert len(chunks) > 1

    for previous, current in zip(
        chunks,
        chunks[1:],
    ):
        overlap = previous[-10:]

        assert overlap in current
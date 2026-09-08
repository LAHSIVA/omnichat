import pytest

from ai.retrieval.relevance import RelevanceEvaluator


class FakeChunk:
    def __init__(self, distance):
        self.distance = distance


def test_empty_chunks_are_not_relevant():
    evaluator = RelevanceEvaluator(max_distance=0.50)

    assert evaluator.is_relevant([]) is False


def test_chunk_within_threshold_is_relevant():
    evaluator = RelevanceEvaluator(max_distance=0.50)
    chunks = [FakeChunk(distance=0.30)]

    assert evaluator.is_relevant(chunks) is True


def test_chunk_at_threshold_is_relevant():
    evaluator = RelevanceEvaluator(max_distance=0.50)
    chunks = [FakeChunk(distance=0.50)]

    assert evaluator.is_relevant(chunks) is True


def test_chunk_above_threshold_is_not_relevant():
    evaluator = RelevanceEvaluator(max_distance=0.50)
    chunks = [FakeChunk(distance=0.51)]

    assert evaluator.is_relevant(chunks) is False


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValueError):
        RelevanceEvaluator(max_distance=0)


def test_relevance_is_based_on_best_chunk():
    evaluator = RelevanceEvaluator(max_distance=0.50)

    chunks = [
        FakeChunk(distance=0.60),
        FakeChunk(distance=0.20),
    ]

    assert evaluator.is_relevant(chunks) is False

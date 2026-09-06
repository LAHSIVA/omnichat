from types import SimpleNamespace

from ai.retrieval.service import RetrievalService


class FakeKnowledgeSearch:
    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, *, query, user, limit):
        return self.chunks


class FakeRelevanceEvaluator:
    def __init__(self, result):
        self.result = result

    def is_relevant(self, chunks):
        return self.result


def test_retrieval_service_returns_relevant_result():
    chunks = [
        SimpleNamespace(distance=0.20),
    ]

    service = RetrievalService(
        knowledge_search=FakeKnowledgeSearch(chunks),
        relevance_evaluator=FakeRelevanceEvaluator(True),
    )

    result = service.retrieve(
        query="What database is used?",
        user=object(),
        limit=5,
    )

    assert result.chunks == chunks
    assert result.is_relevant is True


def test_retrieval_service_returns_general_chat_result():
    chunks = [
        SimpleNamespace(distance=0.70),
    ]

    service = RetrievalService(
        knowledge_search=FakeKnowledgeSearch(chunks),
        relevance_evaluator=FakeRelevanceEvaluator(False),
    )

    result = service.retrieve(
        query="Who won the World Cup?",
        user=object(),
        limit=5,
    )

    assert result.chunks == chunks
    assert result.is_relevant is False

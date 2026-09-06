import pytest
from knowledge.models import Document, DocumentChunk

class FakeKnowledgeSearch:
    """Fake knowledge search used by unit tests."""

    def search(self, query, user, limit=5):
        return []


@pytest.fixture(autouse=True)
def disable_real_knowledge_search(monkeypatch):
    """
    Prevent unit tests from contacting Ollama.

    RAG-specific tests that explicitly pass their own
    knowledge_search dependency are unaffected.
    """
    monkeypatch.setattr(
        "ai.orchestrator.KnowledgeSearchService",
        FakeKnowledgeSearch,
    )

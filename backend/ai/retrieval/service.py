from ai.domain.retrieval import RetrievalResult
from ai.retrieval.relevance import RelevanceEvaluator


class RetrievalService:
    """Retrieves relevant knowledge for a user's query."""

    def __init__(
        self,
        knowledge_search,
        relevance_evaluator: RelevanceEvaluator,
    ) -> None:
        self.knowledge_search = knowledge_search
        self.relevance_evaluator = relevance_evaluator

    def retrieve(
        self,
        *,
        query: str,
        user,
        limit: int,
    ) -> RetrievalResult:
        """Retrieve document chunks and evaluate their relevance."""

        chunks = self.knowledge_search.search(
            query=query,
            user=user,
            limit=limit,
        )

        return RetrievalResult(
            chunks=chunks,
            is_relevant=self.relevance_evaluator.is_relevant(chunks),
        )

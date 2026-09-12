from ai.domain.retrieval import RetrievalResult
from ai.retrieval.query_builder import RetrievalQueryBuilder
from ai.retrieval.relevance import RelevanceEvaluator


class RetrievalService:
    """Retrieves relevant knowledge for a user's query."""

    def __init__(
        self,
        knowledge_search,
        relevance_evaluator: RelevanceEvaluator,
        query_builder: RetrievalQueryBuilder | None = None,
    ) -> None:
        self.knowledge_search = knowledge_search
        self.relevance_evaluator = relevance_evaluator
        self.query_builder = query_builder or RetrievalQueryBuilder()

    def retrieve(
        self,
        *,
        query: str,
        user,
        limit: int,
        history=None,
    ) -> RetrievalResult:
        """Build a self-contained query, retrieve chunks, and evaluate relevance."""

        history = history or []

        retrieval_query = self.query_builder.build(
            content=query,
            history=history,
        )

        chunks = self.knowledge_search.search(
            query=retrieval_query,
            user=user,
            limit=limit,
        )

        return RetrievalResult(
            chunks=chunks,
            is_relevant=self.relevance_evaluator.is_relevant(chunks),
        )

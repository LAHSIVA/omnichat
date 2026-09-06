class RelevanceEvaluator:
    """Determines whether retrieved document context is relevant."""

    def __init__(self, max_distance: float) -> None:
        if max_distance <= 0:
            raise ValueError(
                "max_distance must be greater than zero"
            )

        self.max_distance = max_distance

    def is_relevant(self, chunks) -> bool:
        """Return whether the best retrieved chunk is relevant."""

        if not chunks:
            return False

        return chunks[0].distance <= self.max_distance

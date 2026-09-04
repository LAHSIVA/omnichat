def generate_conversation_title(content: str) -> str:
    """Generate a short deterministic title from the first user message."""

    title = " ".join(content.strip().split())

    if len(title) <= 60:
        return title

    return f"{title[:57].rstrip()}..."
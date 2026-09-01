class LLMError(Exception):
    """Base exception for LLM-related failures."""

class ContextLimitError(LLMError):
    """The requested context cannot fit within the configured limit."""

class LLMAuthenticationError(LLMError):
    """The LLM provider rejected the configured credentials."""


class LLMRateLimitError(LLMError):
    """The LLM provider rate-limited the request."""


class LLMTimeoutError(LLMError):
    """The LLM provider request timed out."""


class LLMProviderError(LLMError):
    """The LLM provider failed unexpectedly."""
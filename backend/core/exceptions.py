from rest_framework.response import Response
from rest_framework.views import exception_handler

from ai.domain.exceptions import (
    LLMAuthenticationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)


def custom_exception_handler(exc, context):
    if isinstance(exc, LLMRateLimitError):
        return Response(
            {
                "detail": "The AI service is temporarily rate limited."
            },
            status=429,
        )

    if isinstance(exc, LLMTimeoutError):
        return Response(
            {
                "detail": "The AI service timed out."
            },
            status=504,
        )

    if isinstance(exc, LLMAuthenticationError):
        return Response(
            {
                "detail": "The AI service is unavailable."
            },
            status=503,
        )

    if isinstance(exc, LLMProviderError):
        return Response(
            {
                "detail": "The AI service is temporarily unavailable."
            },
            status=503,
        )

    return exception_handler(
        exc,
        context,
    )
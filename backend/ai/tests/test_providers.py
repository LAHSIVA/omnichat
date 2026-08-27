from types import SimpleNamespace

from ai.domain.types import ChatMessage
from ai.providers.fake import FakeLLMProvider
from ai.providers.freellmapi import FreeLLMAPIProvider


# ... keep your existing tests ...


def test_freellmapi_provider_omits_max_tokens_when_not_provided(
    monkeypatch,
):
    captured_kwargs = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured_kwargs.update(kwargs)

            return SimpleNamespace(
                model="gemini-3-flash-preview",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Test response",
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=None,
            )

    class FakeClient:
        def __init__(self):
            self.chat = SimpleNamespace(
                completions=FakeCompletions(),
            )

    fake_client = FakeClient()

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = fake_client

    response = provider.generate(
        [
            ChatMessage(
                role="user",
                content="Hello",
            )
        ],
        model="gemini-3-flash-preview",
    )

    assert response.content == "Test response"

    assert "max_tokens" not in captured_kwargs

def test_freellmapi_provider_sends_max_tokens_when_provided():
    captured_kwargs = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured_kwargs.update(kwargs)

            return SimpleNamespace(
                model="gemini-3-flash-preview",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Test response",
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=None,
            )

    class FakeClient:
        def __init__(self):
            self.chat = SimpleNamespace(
                completions=FakeCompletions(),
            )

    provider = FreeLLMAPIProvider(
        api_key="test-api-key",
        base_url="http://test-server/v1",
    )

    provider.client = FakeClient()

    provider.generate(
        [
            ChatMessage(
                role="user",
                content="Hello",
            )
        ],
        model="gemini-3-flash-preview",
        max_tokens=100,
    )

    assert captured_kwargs["max_tokens"] == 100
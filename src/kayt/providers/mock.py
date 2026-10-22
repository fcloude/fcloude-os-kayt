"""Fake providers: deterministic stand-ins used until a real model is wired in."""

from kayt.providers.base import Provider

RESPONSE = "mock response"

#: The fixed reply of the action mock: valid JSON, naming ``grant_1``.
ACTION_REPLY = '{"tool":"summarize_text","grant_id":"grant_1"}'


class MockProvider(Provider):
    """Deterministic stand-in used until a real model is wired in."""

    name = "mock"

    def respond(self, prompt: str) -> str:
        """Ignore the prompt and return the fixed reply."""
        return RESPONSE


class MockActionProvider(Provider):
    """A fake model that always proposes one valid action (name: ``mock``).

    Unlike ``MockProvider`` this returns the JSON the schema expects, so the
    real loop can run end to end without a model.
    """

    name = "mock"

    def respond(self, prompt: str) -> str:
        """Ignore the prompt and return the fixed action JSON."""
        return ACTION_REPLY

"""A fake provider that always gives the same answer."""

from kayt.providers.base import Provider

RESPONSE = "mock response"


class MockProvider(Provider):
    """Deterministic stand-in used until a real model is wired in."""

    name = "mock"

    def respond(self, prompt: str) -> str:
        """Ignore the prompt and return the fixed reply."""
        return RESPONSE

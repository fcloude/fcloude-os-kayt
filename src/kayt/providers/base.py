"""The interface every KAYT model backend must satisfy."""

from abc import ABC, abstractmethod


class Provider(ABC):
    """Something that turns a prompt into a reply."""

    name: str

    @abstractmethod
    def respond(self, prompt: str) -> str:
        """Return the reply to ``prompt``."""
        raise NotImplementedError

"""The shared input rules KAYT accepts.

File reading now lives in `kayt.grants`, which reuses these constants and
raises `InputError` (or its subclass `GrantError`).
"""

MAX_BYTES = 100 * 1024  # 100 KB
SUFFIXES = (".txt", ".md")


class InputError(Exception):
    """A problem with the input that the user can fix."""


def check_question(question: str) -> str:
    """Reject a question that is empty or only whitespace."""
    if not question.strip():
        raise InputError("question is empty")
    return question

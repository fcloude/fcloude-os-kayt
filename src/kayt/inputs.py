"""Reading and checking the inputs KAYT accepts."""

from pathlib import Path

MAX_BYTES = 100 * 1024  # 100 KB
SUFFIXES = (".txt", ".md")


class InputError(Exception):
    """A problem with the input that the user can fix."""


def check_question(question: str) -> str:
    """Reject a question that is empty or only whitespace."""
    if not question.strip():
        raise InputError("question is empty")
    return question


def read_file(path: str) -> str:
    """Read a small UTF-8 text file, or raise InputError with one reason."""
    candidate = Path(path)
    if not candidate.exists():
        raise InputError(f"file not found: {path}")
    if not candidate.is_file():
        raise InputError(f"not a regular file: {path}")
    if candidate.suffix.lower() not in SUFFIXES:
        raise InputError(f"unsupported file type: {path} (use .txt or .md)")
    try:
        if candidate.stat().st_size > MAX_BYTES:
            raise InputError(f"file too large: {path} (limit is 100 KB)")
        data = candidate.read_bytes()
    except OSError:
        raise InputError(f"cannot read file: {path}") from None
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError(f"file is not valid UTF-8: {path}") from None
    if not content:
        raise InputError(f"file is empty: {path}")
    return content

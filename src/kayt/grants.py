"""Session-only file grants, the capability layer from the threat model.

A grant is created from a path the *user* chose. Nothing else — never a model —
supplies a path here (threat model T3). Symlinks are rejected and the file is
opened exactly once, with the regular-file check performed on the open handle
itself, so the check and the read cannot disagree (threat model T4).
"""

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from kayt.inputs import MAX_BYTES, SUFFIXES, InputError


class GrantError(InputError):
    """A problem with a grant: a bad file, an unknown id, or an expired grant."""


@dataclass(frozen=True)
class Grant:
    """An opaque handle to one file the user picked."""

    id: str
    path: Path
    size: int


class GrantStore:
    """Grants valid for this session only: alive until ``clear()`` is called."""

    def __init__(self) -> None:
        self._grants: dict[str, Grant] = {}
        self._contents: dict[str, str] = {}
        self._next_id = 1

    def create(self, path: str | Path) -> tuple[Grant, str]:
        """Grant a user-chosen file, returning the grant and its text."""
        candidate = Path(path)
        if candidate.is_symlink():
            raise GrantError(f"symlink not allowed: {path}")
        if not candidate.exists():
            raise GrantError(f"file not found: {path}")
        if not candidate.is_file():
            raise GrantError(f"not a regular file: {path}")
        if candidate.suffix.lower() not in SUFFIXES:
            raise GrantError(f"unsupported file type: {path} (use .txt or .md)")

        resolved = candidate.resolve()
        try:
            with open(resolved, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise GrantError(f"not a regular file after open: {path}")
                if info.st_size > MAX_BYTES:
                    raise GrantError(f"file too large: {path} (limit is 100 KB)")
                data = handle.read()
        except OSError:
            raise GrantError(f"cannot read file: {path}") from None

        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            raise GrantError(f"file is not valid UTF-8: {path}") from None
        if not content:
            raise GrantError(f"file is empty: {path}")

        grant = Grant(id=f"grant_{self._next_id}", path=resolved, size=info.st_size)
        self._next_id += 1
        self._grants[grant.id] = grant
        self._contents[grant.id] = content
        return grant, content

    def lookup(self, grant_id: str) -> Grant:
        """Return the grant for ``grant_id``, or raise if unknown or cleared."""
        try:
            return self._grants[grant_id]
        except KeyError:
            raise GrantError(f"unknown grant: {grant_id}") from None

    def read(self, grant_id: str) -> str:
        """Return the text captured when the grant was created."""
        try:
            return self._contents[grant_id]
        except KeyError:
            raise GrantError(f"unknown grant: {grant_id}") from None

    def clear(self) -> None:
        """End the session: every grant expires and its id stays dead."""
        self._grants.clear()
        self._contents.clear()

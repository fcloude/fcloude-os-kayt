"""Session-only file grants, the capability layer from the threat model.

A grant is created from a path the *user* chose. Nothing else — never a model —
supplies a path here (threat model T3). Symlinks are rejected up front and the
file is opened with ``O_NOFOLLOW`` (where the platform has it) so the final path
component cannot be swapped for a link. ``O_NONBLOCK`` (also where available)
keeps a named pipe from hanging the open. The regular-file check is then
performed on the open handle itself, and the read is capped at one byte past
the limit, so the check and the read cannot disagree (threat model T4).

Creation fails closed: any error — expected or not — surfaces as a ``GrantError``
with a one-line message, and a grant is stored only after every step succeeded.
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


def _read_upto(fd: int, limit: int) -> bytes:
    """Read at most ``limit`` bytes from an open file description."""
    chunks: list[bytes] = []
    remaining = limit
    while remaining > 0:
        chunk = os.read(fd, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class GrantStore:
    """Grants valid for this session only: alive until ``clear()`` is called."""

    def __init__(self) -> None:
        self._grants: dict[str, Grant] = {}
        self._contents: dict[str, str] = {}
        self._next_id = 1

    def create(self, path: str | Path) -> tuple[Grant, str]:
        """Grant a user-chosen file, returning the grant and its text.

        Fails closed: any error becomes a GrantError and stores no grant.
        """
        try:
            candidate = Path(path)
            if candidate.is_symlink():
                raise GrantError(f"symlink not allowed: {path}")
            if not candidate.exists():
                raise GrantError(f"file not found: {path}")
            if not candidate.is_file():
                raise GrantError(f"not a regular file: {path}")
            if candidate.suffix.lower() not in SUFFIXES:
                raise GrantError(
                    f"unsupported file type: {path} (use .txt or .md)"
                )

            resolved = candidate.resolve()
            flags = (
                os.O_RDONLY
                | getattr(os, "O_BINARY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0)
            )
            fd = os.open(resolved, flags)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    raise GrantError(f"not a regular file after open: {path}")
                if info.st_size > MAX_BYTES:
                    raise GrantError(f"file too large: {path} (limit is 100 KB)")
                data = _read_upto(fd, MAX_BYTES + 1)
            finally:
                os.close(fd)

            if len(data) > MAX_BYTES:
                raise GrantError(f"file too large: {path} (limit is 100 KB)")
            try:
                content = data.decode("utf-8")
            except UnicodeDecodeError:
                raise GrantError(f"file is not valid UTF-8: {path}") from None
            if not content:
                raise GrantError(f"file is empty: {path}")
        except GrantError:
            raise
        except OSError:
            raise GrantError(f"cannot read file: {path}") from None
        except Exception:
            raise GrantError(f"cannot read file: {path}") from None

        grant = Grant(
            id=f"grant_{self._next_id}", path=resolved, size=info.st_size
        )
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

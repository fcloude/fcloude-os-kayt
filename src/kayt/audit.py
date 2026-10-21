"""Append-only audit log: one JSON line per event (threat model T5).

What goes in: metadata only -- a UTC timestamp, the event name, whether the
action was allowed, a short outcome, the tool, and the grant id. There is no
free-text field, so file contents, keys, and passwords have nowhere to go.

Where the log lives: the caller gives the path; there is deliberately no
default, and in particular none inside the source tree. A sensible home is the
user's own data directory -- ``%LOCALAPPDATA%\\kayt\\audit.jsonl`` on Windows or
``~/.local/state/kayt/audit.jsonl`` on Linux -- whose parent directory must
already exist. Tests and demos pass a temporary path.

How to clear it: ``AuditLog(path).clear()`` deletes the file; recording again
simply starts a new one, and clearing a missing file is not an error.

Every string field is flattened to one line and capped at ``MAX_FIELD_CHARS``,
so one ``record`` call writes exactly one line even when the values are hostile
(log-injection defence). A failed write never reaches the caller: it is counted
in ``failures`` so the problem stays visible instead of vanishing.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

MAX_FIELD_CHARS = 100


def _flatten(value: object) -> str:
    """Turn one field into a short single-line string."""
    try:
        text = value if isinstance(value, str) else str(value)
    except Exception:
        return ""
    single_line = "".join(
        " " if not character.isprintable() else character for character in text
    )
    return single_line[:MAX_FIELD_CHARS]


class AuditLog:
    """Append one JSON line per ``record`` call. Never raises at the caller."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.failures = 0

    @staticmethod
    def _line(
        event: object,
        allowed: object,
        outcome: object,
        tool: object,
        grant_id: object,
    ) -> str:
        """Build the one line for this event, with fixed keys and order."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": _flatten(event),
            "allowed": bool(allowed),
            "outcome": _flatten(outcome),
            "tool": _flatten(tool),
            "grant_id": _flatten(grant_id),
        }
        return json.dumps(entry)

    def record(
        self,
        event: str,
        allowed: bool,
        outcome: str,
        tool: str = "",
        grant_id: str = "",
    ) -> None:
        """Append one JSON line. A failed write is counted, never raised."""
        try:
            line = self._line(event, allowed, outcome, tool, grant_id)
        except Exception:
            self.failures += 1
            return

        try:
            # Opened per call and closed immediately: no handle outlives a
            # record, so nothing stays buffered for a later crash to lose.
            # newline="\n" keeps one record equal to one LF-terminated line
            # on every platform, which is what the one-line rule promises.
            with open(self.path, "a", encoding="utf-8", newline="\n") as handle:
                handle.write(line + "\n")
        except Exception:
            self.failures += 1

    def clear(self) -> None:
        """Delete the log file; a missing file is not an error."""
        try:
            self.path.unlink(missing_ok=True)
        except Exception:
            self.failures += 1

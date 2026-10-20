"""Strict validation of the model's structured output (threat model T2).

Model text is untrusted: it may be truncated, malformed, or actively hostile.
``parse_action`` accepts exactly one shape and refuses everything else. Error
messages name the category of problem and never quote the raw input, so model
text cannot leak into errors, logs, or a terminal.
"""

import json
import re
from dataclasses import dataclass

MAX_RAW_BYTES = 10 * 1024
GRANT_ID_PATTERN = re.compile(r"grant_[0-9]+")
ALLOWED_TOOLS = ("summarize_text",)


class SchemaError(Exception):
    """A problem with model output that KAYT refuses to interpret."""


@dataclass(frozen=True)
class Action:
    """The one action a validated model output asks for."""

    tool: str
    grant_id: str


def _object_without_duplicates(pairs: list[tuple[str, object]]) -> dict:
    """Build an object, refusing repeated keys."""
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise SchemaError("model output has duplicate keys")
        seen[key] = value
    return seen


def parse_action(raw: str) -> Action:
    """Validate raw model text and return the single action it describes.

    Fails closed: every refusal is a one-line SchemaError that never echoes
    the raw input.
    """
    try:
        if len(raw.encode("utf-8")) > MAX_RAW_BYTES:
            raise SchemaError("model output is too large")

        try:
            data = json.loads(
                raw, object_pairs_hook=_object_without_duplicates
            )
        except SchemaError:
            raise
        except ValueError:
            raise SchemaError("model output is not valid JSON") from None

        if not isinstance(data, dict):
            raise SchemaError("model output must be a JSON object")
        if set(data) != {"tool", "grant_id"}:
            if {"tool", "grant_id"} - set(data):
                raise SchemaError("model output is missing a field")
            raise SchemaError("model output has an unexpected field")

        tool = data["tool"]
        grant_id = data["grant_id"]
        if not isinstance(tool, str) or not isinstance(grant_id, str):
            raise SchemaError("model output fields must be strings")
        if tool not in ALLOWED_TOOLS:
            raise SchemaError("model output asks for an unknown tool")
        if not GRANT_ID_PATTERN.fullmatch(grant_id):
            raise SchemaError("model output has an invalid grant reference")
    except SchemaError:
        raise
    except Exception:
        raise SchemaError("could not interpret model output") from None

    return Action(tool=tool, grant_id=grant_id)

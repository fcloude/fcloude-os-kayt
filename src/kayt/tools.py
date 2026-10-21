"""The narrow tool gateway (Plan §3.1 layer 6).

Every capability KAYT has is a hand-written function in one small dict. The
gateway trusts nobody: it asks the policy engine itself, even when the caller
claims to have asked already, and it refuses anything the registry does not
hold. There is no dynamic dispatch, no shell, and no filesystem access here --
content comes only from a live grant, and nothing longer than
``MAX_OUTPUT_CHARS`` ever leaves, whatever a future tool tries to return.

Failure is a value, not an exception: every path returns a ``ToolResult`` with
a fixed-string error that never echoes file content or exception text.
"""

from dataclasses import dataclass

from kayt import policy

SUMMARY_CHARS = 200
SUMMARY_PREFIX = "Summary: "
MAX_OUTPUT_CHARS = 2000  # gateway cap: applies to every tool, present or future


@dataclass(frozen=True)
class ToolResult:
    """The outcome of one tool call: a success value or a one-line error."""

    ok: bool
    output: str
    error: str


def _summarize_text(store: object, grant_id: str) -> str:
    """Return a deterministic placeholder summary of the granted text."""
    content = store.read(grant_id)
    return SUMMARY_PREFIX + content[:SUMMARY_CHARS]


TOOLS = {"summarize_text": _summarize_text}


def execute(action: object, store: object) -> ToolResult:
    """Run the action's tool if policy allows it. Never raises."""
    try:
        if not policy.decide(action, store).allowed:
            return ToolResult(False, "", "refused: policy did not allow it")
        function = TOOLS.get(action.tool)
        if function is None:
            return ToolResult(False, "", "failed: no such tool is registered")
        output = function(store, action.grant_id)
        if not isinstance(output, str):
            return ToolResult(False, "", "failed: the tool returned no text")
        # The cap lives here, not in each tool, so no future tool can skip it.
        return ToolResult(True, output[:MAX_OUTPUT_CHARS], "")
    except Exception:
        return ToolResult(False, "", "failed: the tool could not run")

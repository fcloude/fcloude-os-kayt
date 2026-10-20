"""Deterministic, default-deny policy (Plan §3.1 layer 5).

The policy engine is plain code. It cannot be talked to, has no override, and
never trusts the model: it decides from a validated ``Action`` and the live
grants only. Its allowlist is deliberately separate from the schema's, so the
two layers fail independently. Reasons are fixed strings, so nothing from the
model can echo back.
"""

from dataclasses import dataclass

from kayt.schema import Action

POLICY_ALLOWED_TOOLS = ("summarize_text",)


@dataclass(frozen=True)
class Decision:
    """The verdict for one action, with a fixed-string reason."""

    allowed: bool
    reason: str


def decide(action: object, store: object) -> Decision:
    """Return ALLOW, or DENY with a reason. Never raises."""
    try:
        if not isinstance(action, Action):
            return Decision(False, "denied: action is not a validated action")
        if action.tool not in POLICY_ALLOWED_TOOLS:
            return Decision(False, "denied: tool is not permitted by policy")
        try:
            store.lookup(action.grant_id)
        except Exception:
            return Decision(
                False, "denied: grant is unknown, expired, or unusable"
            )
    except Exception:
        return Decision(False, "denied: policy could not decide")
    return Decision(True, "allowed: tool and grant both check out")

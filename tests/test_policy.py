import inspect
from dataclasses import FrozenInstanceError

import pytest

import kayt.policy as policy
import kayt.schema as schema
from kayt.grants import GrantStore
from kayt.policy import Decision, decide
from kayt.schema import Action


def make_store(tmp_path):
    """A store holding exactly one live grant, ``grant_1``."""
    path = tmp_path / "notes.txt"
    path.write_text("hello world", encoding="utf-8")
    store = GrantStore()
    grant, _ = store.create(path)
    return store, grant


def test_allowed_action_is_permitted(tmp_path):
    store, grant = make_store(tmp_path)
    decision = decide(Action(tool="summarize_text", grant_id=grant.id), store)
    assert decision.allowed is True
    assert decision.reason == "allowed: tool and grant both check out"


def test_tool_outside_policy_allowlist_denied(tmp_path):
    store, grant = make_store(tmp_path)
    decision = decide(Action(tool="run_shell", grant_id=grant.id), store)
    assert decision.allowed is False
    assert "run_shell" not in decision.reason  # never echo model text


def test_policy_allowlist_is_separate_from_schemas():
    assert policy.POLICY_ALLOWED_TOOLS is not schema.ALLOWED_TOOLS
    assert set(policy.POLICY_ALLOWED_TOOLS) == set(schema.ALLOWED_TOOLS)


def test_missing_grant_denied(tmp_path):
    store, _ = make_store(tmp_path)  # only grant_1 exists
    decision = decide(Action(tool="summarize_text", grant_id="grant_2"), store)
    assert decision.allowed is False


def test_invented_grant_denied(tmp_path):
    store, _ = make_store(tmp_path)
    decision = decide(Action(tool="summarize_text", grant_id="grant_99"), store)
    assert decision.allowed is False


def test_cleared_grant_denied(tmp_path):
    store, grant = make_store(tmp_path)
    assert decide(Action("summarize_text", grant.id), store).allowed is True
    store.clear()
    assert decide(Action("summarize_text", grant.id), store).allowed is False


def test_none_action_denied(tmp_path):
    store, _ = make_store(tmp_path)
    decision = decide(None, store)
    assert decision.allowed is False
    assert decision.reason == "denied: action is not a validated action"


@pytest.mark.parametrize(
    "impostor",
    ["summarize_text", {"tool": "summarize_text", "grant_id": "grant_1"}, object()],
)
def test_wrong_type_action_denied(tmp_path, impostor):
    store, _ = make_store(tmp_path)
    assert decide(impostor, store).allowed is False


def test_store_exception_denied(tmp_path, monkeypatch):
    store, grant = make_store(tmp_path)

    def explode(grant_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(store, "lookup", explode)
    decision = decide(Action("summarize_text", grant.id), store)
    assert decision.allowed is False
    assert "boom" not in decision.reason


def test_decision_is_frozen():
    decision = decide(None, None)
    with pytest.raises(FrozenInstanceError):
        decision.allowed = True


def test_no_store_denied_without_raising():
    decision = decide(Action("summarize_text", "grant_1"), None)
    assert decision.allowed is False
    assert decision.reason.startswith("denied")


def test_policy_imports_no_provider_and_touches_no_files():
    imports = [
        line.strip()
        for line in inspect.getsource(policy).splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    assert imports == [
        "from dataclasses import dataclass",
        "from kayt.schema import Action",
    ]

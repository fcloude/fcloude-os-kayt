import ast
import inspect
from dataclasses import FrozenInstanceError

import pytest

import kayt.tools as tools
from kayt.grants import GrantStore
from kayt.policy import decide
from kayt.schema import Action
from kayt.tools import ToolResult, execute


def make_store(tmp_path, text="hello world"):
    """A store holding exactly one live grant, ``grant_1``."""
    path = tmp_path / "notes.txt"
    path.write_text(text, encoding="utf-8")
    store = GrantStore()
    grant, _ = store.create(path)
    return store, grant


def allowed_action(grant):
    return Action(tool="summarize_text", grant_id=grant.id)


def test_summarize_text_succeeds(tmp_path):
    store, grant = make_store(tmp_path, "hello world")
    result = execute(allowed_action(grant), store)
    assert result == ToolResult(True, "Summary: hello world", "")
    assert result.ok is True
    assert result.error == ""


def test_summary_is_deterministic(tmp_path):
    store, grant = make_store(tmp_path, "repeatable text")
    first = execute(allowed_action(grant), store)
    second = execute(allowed_action(grant), store)
    assert first == second
    assert first.output == "Summary: repeatable text"


def test_tool_outside_policy_allowlist_denied(tmp_path):
    store, grant = make_store(tmp_path)
    result = execute(Action(tool="run_shell", grant_id=grant.id), store)
    assert result.ok is False
    assert result.output == ""
    assert result.error == "refused: policy did not allow it"
    assert "run_shell" not in result.error  # never echo model text


def test_cleared_grant_denied_at_execution_time(tmp_path):
    store, grant = make_store(tmp_path)
    store.clear()
    result = execute(allowed_action(grant), store)
    assert result.ok is False
    assert result.output == ""
    assert result.error.startswith("refused")


def test_grant_cleared_between_callers_check_and_execute(tmp_path):
    store, grant = make_store(tmp_path)
    action = allowed_action(grant)
    assert decide(action, store).allowed is True  # a stale "allowed" in hand
    store.clear()  # the session ends in between
    result = execute(action, store)
    # execute asks policy itself, so the caller's stale verdict buys nothing.
    assert result.ok is False
    assert result.output == ""
    assert result.error == "refused: policy did not allow it"


def test_none_action_denied_without_raising(tmp_path):
    store, _ = make_store(tmp_path)
    result = execute(None, store)
    assert result.ok is False
    assert result.output == ""
    assert result.error == "refused: policy did not allow it"


def test_none_store_denied_without_raising(tmp_path):
    _, grant = make_store(tmp_path)
    result = execute(allowed_action(grant), None)
    assert result.ok is False
    assert result.error.count("\n") == 0


def test_tool_function_that_raises_becomes_generic_failure(
    tmp_path, monkeypatch
):
    store, grant = make_store(tmp_path)

    def explode(store, grant_id):
        raise RuntimeError("boom LEAKME")

    monkeypatch.setitem(tools.TOOLS, "summarize_text", explode)
    result = execute(allowed_action(grant), store)
    assert result.ok is False
    assert result.output == ""
    assert result.error == "failed: the tool could not run"
    assert result.error.count("\n") == 0
    assert "LEAKME" not in result.error and "RuntimeError" not in result.error


def test_tool_returning_non_text_fails(tmp_path, monkeypatch):
    store, grant = make_store(tmp_path)
    monkeypatch.setitem(tools.TOOLS, "summarize_text", lambda store, gid: None)
    result = execute(allowed_action(grant), store)
    assert result.ok is False
    assert result.output == ""
    assert result.error == "failed: the tool returned no text"


def test_allowed_tool_missing_from_registry_fails(tmp_path, monkeypatch):
    store, grant = make_store(tmp_path)
    monkeypatch.delitem(tools.TOOLS, "summarize_text")
    result = execute(allowed_action(grant), store)
    assert result.ok is False
    assert result.output == ""
    assert result.error == "failed: no such tool is registered"


def test_output_never_carries_more_than_200_characters(tmp_path):
    store, grant = make_store(tmp_path, "a" * 200 + "TAILMUSTNOTAPPEAR")
    result = execute(allowed_action(grant), store)
    assert result.ok is True
    assert result.output == "Summary: " + "a" * 200
    assert len(result.output) == len("Summary: ") + 200
    assert "TAILMUSTNOTAPPEAR" not in result.output


def test_gateway_caps_output_for_every_tool(tmp_path, monkeypatch):
    store, grant = make_store(tmp_path)
    monkeypatch.setitem(tools.TOOLS, "summarize_text", lambda s, g: "b" * 5000)
    result = execute(allowed_action(grant), store)
    assert result.ok is True
    assert tools.MAX_OUTPUT_CHARS == 2000
    assert result.output == "b" * 2000
    assert len(result.output) == tools.MAX_OUTPUT_CHARS


def test_short_content_is_summarised_whole(tmp_path):
    store, grant = make_store(tmp_path, "short")
    assert execute(allowed_action(grant), store).output == "Summary: short"


def test_tool_result_is_frozen():
    result = ToolResult(True, "out", "")
    with pytest.raises(FrozenInstanceError):
        result.ok = False


def test_tools_imports_only_dataclasses_and_policy():
    imports = [
        line.strip()
        for line in inspect.getsource(tools).splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    assert imports == [
        "from dataclasses import dataclass",
        "from kayt import policy",
    ]


def test_tools_calls_no_escape_hatch_builtin():
    called = {
        node.func.id
        for node in ast.walk(ast.parse(inspect.getsource(tools)))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called.isdisjoint({"eval", "exec", "open", "compile", "__import__"})

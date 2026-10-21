import ast
import inspect
import json
from datetime import datetime

import pytest

import kayt.audit as audit
from kayt.audit import MAX_FIELD_CHARS, AuditLog

FIELDS = {"timestamp", "event", "allowed", "outcome", "tool", "grant_id"}


def lines_of(path):
    return path.read_text(encoding="utf-8").splitlines()


def make_log(tmp_path):
    return AuditLog(tmp_path / "audit.jsonl")


def test_one_line_per_call(tmp_path):
    log = make_log(tmp_path)
    log.record("decide", True, "allowed")
    log.record("execute", True, "ok")
    log.record("execute", False, "refused")
    lines = lines_of(log.path)
    assert len(lines) == 3
    assert all(line.strip() for line in lines)
    assert log.path.read_bytes().count(b"\n") == 3


def test_every_line_is_valid_json(tmp_path):
    log = make_log(tmp_path)
    log.record("decide", True, "allowed")
    log.record("execute", False, "refused: policy did not allow it")
    entries = [json.loads(line) for line in lines_of(log.path)]
    assert len(entries) == 2
    assert entries[0]["allowed"] is True
    assert entries[1]["allowed"] is False


def test_no_field_outside_the_allowed_set(tmp_path):
    log = make_log(tmp_path)
    log.record("decide", True, "allowed", tool="summarize_text", grant_id="g")
    entry = json.loads(lines_of(log.path)[0])
    assert set(entry) == FIELDS
    assert isinstance(entry["allowed"], bool)
    for field in ("timestamp", "event", "outcome", "tool", "grant_id"):
        assert isinstance(entry[field], str)


def test_newline_injection_stays_on_one_line(tmp_path):
    log = make_log(tmp_path)
    log.record(
        "decide\n{\"allowed\": true}",
        False,
        "refused\r\ninjected event\r",
    )
    lines = lines_of(log.path)
    assert len(lines) == 1
    raw = log.path.read_bytes()
    assert raw.count(b"\n") == 1  # one record, one line terminator
    assert b"\r" not in raw
    entry = json.loads(lines[0])
    assert "\n" not in entry["event"] and "\r" not in entry["event"]
    assert "\n" not in entry["outcome"] and "\r" not in entry["outcome"]


def test_control_characters_are_replaced(tmp_path):
    log = make_log(tmp_path)
    log.record("decide", True, "a\x00b\x1b[31mc\td\x7fe")
    entry = json.loads(lines_of(log.path)[0])
    assert all(character.isprintable() for character in entry["outcome"])
    assert entry["outcome"] == "a b [31mc d e"


def test_long_values_are_truncated(tmp_path):
    log = make_log(tmp_path)
    log.record("e" * 500, True, "o" * 500, tool="t" * 500, grant_id="g" * 500)
    entry = json.loads(lines_of(log.path)[0])
    for field in ("event", "outcome", "tool", "grant_id"):
        assert entry[field] == field[0] * MAX_FIELD_CHARS
        assert len(entry[field]) == 100


def test_file_content_marker_is_truncated_never_expanded(tmp_path):
    log = make_log(tmp_path)
    marker = "SECRET-FILE-CONTENT-" + "z" * 300
    log.record("execute", True, marker)
    entry = json.loads(lines_of(log.path)[0])
    assert entry["outcome"] == marker[:100]
    assert len(entry["outcome"]) == MAX_FIELD_CHARS
    assert marker[100:] not in entry["outcome"]


def test_defaults_are_empty_strings(tmp_path):
    log = make_log(tmp_path)
    log.record("decide", False, "denied")
    entry = json.loads(lines_of(log.path)[0])
    assert entry["tool"] == ""
    assert entry["grant_id"] == ""


def test_timestamp_is_utc_iso(tmp_path):
    log = make_log(tmp_path)
    log.record("decide", True, "allowed")
    stamp = datetime.fromisoformat(json.loads(lines_of(log.path)[0])["timestamp"])
    assert stamp.tzinfo is not None
    assert stamp.utcoffset().total_seconds() == 0


def test_write_failure_does_not_raise_and_counts(tmp_path):
    log = AuditLog(tmp_path)  # a directory cannot be opened for appending
    assert log.failures == 0
    log.record("decide", True, "allowed")
    assert log.failures == 1
    assert tmp_path.is_dir()  # nothing was replaced
    log.record("decide", True, "allowed")
    assert log.failures == 2


def test_clear_deletes_the_log(tmp_path):
    log = make_log(tmp_path)
    log.record("decide", True, "allowed")
    assert log.path.exists()
    log.clear()
    assert not log.path.exists()
    log.clear()  # a missing file is not an error
    assert log.failures == 0


def test_appends_across_instances(tmp_path):
    path = tmp_path / "audit.jsonl"
    AuditLog(path).record("first", True, "allowed")
    AuditLog(path).record("second", False, "refused")
    entries = [json.loads(line) for line in lines_of(path)]
    assert [entry["event"] for entry in entries] == ["first", "second"]


def test_record_after_clear_starts_a_new_file(tmp_path):
    log = make_log(tmp_path)
    log.record("first", True, "allowed")
    log.clear()
    log.record("second", True, "allowed")
    entries = [json.loads(line) for line in lines_of(log.path)]
    assert [entry["event"] for entry in entries] == ["second"]


def test_path_is_required():
    with pytest.raises(TypeError):
        AuditLog()


def test_audit_has_no_shell_and_only_stdlib_imports():
    tree = ast.parse(inspect.getsource(audit))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module)
    assert modules == {"json", "datetime", "pathlib"}

    attributes = {
        f"{node.value.id}.{node.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
    }
    assert "os.system" not in attributes
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called.isdisjoint({"eval", "exec", "__import__", "compile"})

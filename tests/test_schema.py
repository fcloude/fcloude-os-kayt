from dataclasses import FrozenInstanceError

import pytest

import kayt.schema as schema
from kayt.schema import Action, SchemaError, parse_action

VALID = '{"tool": "summarize_text", "grant_id": "grant_1"}'


def test_valid_action_is_parsed():
    action = parse_action(VALID)
    assert action == Action(tool="summarize_text", grant_id="grant_1")


def test_action_is_frozen():
    action = parse_action(VALID)
    with pytest.raises(FrozenInstanceError):
        action.tool = "other"


def test_truncated_json_rejected():
    with pytest.raises(SchemaError, match="not valid JSON"):
        parse_action(VALID[:-10])


def test_extra_field_rejected():
    raw = '{"tool": "summarize_text", "grant_id": "grant_1", "sudo": true}'
    with pytest.raises(SchemaError, match="unexpected field"):
        parse_action(raw)


def test_missing_field_rejected():
    with pytest.raises(SchemaError, match="missing a field"):
        parse_action('{"tool": "summarize_text"}')


def test_wrong_type_rejected():
    with pytest.raises(SchemaError, match="must be strings"):
        parse_action('{"tool": "summarize_text", "grant_id": 42}')
    with pytest.raises(SchemaError, match="must be strings"):
        parse_action('{"tool": ["summarize_text"], "grant_id": "grant_1"}')


def test_unknown_tool_rejected_without_echo():
    raw = '{"tool": "run_shell", "grant_id": "grant_1"}'
    with pytest.raises(SchemaError) as err:
        parse_action(raw)
    message = str(err.value)
    assert "unknown tool" in message
    assert "run_shell" not in message  # raw input is never echoed


def test_path_in_grant_id_rejected():
    raw = '{"tool": "summarize_text", "grant_id": "../../etc/passwd"}'
    with pytest.raises(SchemaError, match="invalid grant reference"):
        parse_action(raw)


def test_oversized_input_rejected_before_parsing():
    raw = VALID + " " * (schema.MAX_RAW_BYTES + 1)
    with pytest.raises(SchemaError, match="too large"):
        parse_action(raw)


def test_duplicate_keys_rejected():
    raw = (
        '{"tool": "summarize_text", "tool": "summarize_text", '
        '"grant_id": "grant_1"}'
    )
    with pytest.raises(SchemaError, match="duplicate keys"):
        parse_action(raw)


@pytest.mark.parametrize("raw", ["[]", "12", "null", '"a string"', "true"])
def test_non_object_json_rejected(raw):
    with pytest.raises(SchemaError, match="must be a JSON object"):
        parse_action(raw)


def test_unexpected_error_fails_closed_without_echo(monkeypatch):
    raw = VALID + " LEAKME"

    def explode(*args, **kwargs):
        raise RuntimeError("boom LEAKME")

    monkeypatch.setattr(schema.json, "loads", explode)
    with pytest.raises(SchemaError) as err:
        parse_action(raw)
    message = str(err.value)
    assert message == "could not interpret model output"
    assert "LEAKME" not in message
    assert message.count("\n") == 0

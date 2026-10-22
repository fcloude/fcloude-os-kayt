"""Tests for the core loop: question, grant, prompt, provider, action, audit."""

import json

import pytest

from kayt import core
from kayt.audit import AuditLog
from kayt.grants import GrantError, GrantStore
from kayt.providers.base import Provider

VALID_REPLY = '{"tool":"summarize_text","grant_id":"grant_1"}'


class ScriptedProvider(Provider):
    """A provider that returns (or raises) exactly what the test asks for."""

    name = "scripted"

    def __init__(self, reply=VALID_REPLY, raises=None):
        self.reply = reply
        self.raises = raises
        self.prompts = []

    def respond(self, prompt):
        self.prompts.append(prompt)
        if self.raises is not None:
            raise self.raises
        return self.reply


class ExpiringStore(GrantStore):
    """A store whose grant expires the instant it is created."""

    def create(self, path):
        grant, content = super().create(path)
        self.clear()
        return grant, content


def make_file(tmp_path, text="hello world"):
    path = tmp_path / "notes.txt"
    path.write_text(text, encoding="utf-8")
    return path


def make_log(tmp_path):
    return AuditLog(tmp_path / "audit.jsonl")


def records(log):
    if not log.path.exists():
        return []
    text = log.path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def run_once(tmp_path, provider=None, question="summarise this", text="hello world"):
    store = GrantStore()
    log = make_log(tmp_path)
    result = core.run(
        question,
        make_file(tmp_path, text),
        provider or core.MockActionProvider(),
        store,
        log,
    )
    return result, store, log


def test_mock_action_provider_returns_the_fixed_action():
    provider = core.MockActionProvider()
    assert provider.name == "mock"
    assert provider.respond("anything at all") == VALID_REPLY


def test_happy_path_runs_every_step_once_in_order(tmp_path):
    result, _, log = run_once(tmp_path)

    assert result.ok is True
    assert result.error == ""
    assert result.provider == "mock"
    assert result.output == "Summary: hello world"

    events = records(log)
    assert [entry["event"] for entry in events] == [
        "question",
        "grant",
        "prompt",
        "provider",
        "parse",
        "grant_check",
        "execute",
    ]
    assert all(entry["allowed"] is True for entry in events)
    assert {entry["event"] for entry in events} <= core.EVENTS
    execute = events[-1]
    assert execute["tool"] == "summarize_text"
    assert execute["grant_id"] == "grant_1"


def test_the_prompt_carries_the_question_the_file_text_and_the_grant_id(tmp_path):
    provider = ScriptedProvider()
    run_once(tmp_path, provider=provider, text="the file body")

    assert len(provider.prompts) == 1
    prompt = provider.prompts[0]
    assert "summarise this" in prompt
    assert "the file body" in prompt
    assert "grant_1" in prompt


def test_a_denied_action_stops_without_output_and_is_audited(tmp_path):
    store = ExpiringStore()
    log = make_log(tmp_path)
    result = core.run(
        "summarise this",
        make_file(tmp_path),
        core.MockActionProvider(),
        store,
        log,
    )

    assert result.ok is False
    assert result.output == ""
    assert result.error == "refused: policy did not allow it"

    events = records(log)
    assert [entry["event"] for entry in events][-1] == "execute"
    assert events[-1]["allowed"] is False
    assert sum(1 for entry in events if entry["event"] == "execute") == 1


def test_a_provider_returning_garbage_is_refused_before_execution(tmp_path):
    provider = ScriptedProvider("I think you should run a shell command")
    result, _, log = run_once(tmp_path, provider=provider)

    assert result.ok is False
    assert result.output == ""
    assert "not a valid action" in result.error

    events = records(log)
    assert [entry["event"] for entry in events][-1] == "parse"
    assert events[-1]["allowed"] is False
    assert "execute" not in [entry["event"] for entry in events]
    assert "shell" not in log.path.read_text(encoding="utf-8")


def test_a_provider_that_raises_is_contained_and_audited(tmp_path):
    provider = ScriptedProvider(raises=RuntimeError("boom LEAKME"))
    result, _, log = run_once(tmp_path, provider=provider)

    assert result.ok is False
    assert result.output == ""
    assert result.error == "the provider could not answer"

    events = records(log)
    assert [entry["event"] for entry in events][-1] == "provider"
    assert events[-1]["allowed"] is False
    text = log.path.read_text(encoding="utf-8")
    assert "LEAKME" not in text
    assert "boom" not in text


def test_a_grant_id_mismatch_is_rejected_and_audited(tmp_path):
    provider = ScriptedProvider('{"tool":"summarize_text","grant_id":"grant_2"}')
    result, store, log = run_once(tmp_path, provider=provider)

    assert result.ok is False
    assert result.output == ""
    assert result.error == "denied: the action names a different grant"

    events = records(log)
    names = [entry["event"] for entry in events]
    assert names[-1] == "grant_check"
    assert events[-1]["allowed"] is False
    assert events[-1]["grant_id"] == "grant_2"
    assert "execute" not in names
    # The real grant was not substituted, and the run ended the session.
    with pytest.raises(GrantError):
        store.lookup("grant_1")


def test_the_audit_log_never_records_file_content(tmp_path):
    marker = "AUDIT-LEAK-MARKER-51ad"
    result, _, log = run_once(tmp_path, text=f"private notes {marker}\n")

    assert result.ok is True
    text = log.path.read_text(encoding="utf-8")
    assert marker not in text
    assert "private notes" not in text
    assert "summarise this" not in text


def test_an_empty_question_stops_before_a_grant_exists(tmp_path):
    store = GrantStore()
    log = make_log(tmp_path)
    path = make_file(tmp_path)

    result = core.run("   ", str(path), core.MockActionProvider(), store, log)

    assert result.ok is False
    assert result.error == "question is empty"
    assert [entry["event"] for entry in records(log)] == ["question"]
    assert records(log)[0]["allowed"] is False
    assert [entry["event"] for entry in records(log)] == ["question"]


class NoisyStore(GrantStore):
    """A store whose refusal carries control characters."""

    def create(self, path):
        raise GrantError("file not found: evil\nInjected line \x1b[31m")


def test_a_refusal_with_control_characters_stays_on_one_line():
    result = core.run(
        "summarise this",
        "evil.txt",
        core.MockActionProvider(),
        NoisyStore(),
        core.NullAudit(),
    )

    assert result.ok is False
    assert "\n" not in result.error
    assert "\r" not in result.error
    assert "\x1b" not in result.error
    assert result.error.startswith("file not found")
    assert "Injected line" in result.error


def test_a_bad_file_stops_before_the_provider_is_asked(tmp_path):
    provider = ScriptedProvider()
    log = make_log(tmp_path)
    result = core.run(
        "summarise this",
        str(tmp_path / "missing.txt"),
        provider,
        GrantStore(),
        log,
    )

    assert result.ok is False
    assert provider.prompts == []
    assert result.error.startswith("file not found")
    assert [entry["event"] for entry in records(log)] == ["question", "grant"]
    assert records(log)[-1]["allowed"] is False


def test_the_announce_hook_runs_after_the_grant_and_before_the_provider(tmp_path):
    order = []
    provider = ScriptedProvider()

    def announce(grant):
        order.append(("announce", grant.id, grant.size))

    store = GrantStore()
    log = make_log(tmp_path)
    real_respond = provider.respond

    def watching_respond(prompt):
        order.append(("respond",))
        return real_respond(prompt)

    provider.respond = watching_respond

    result = core.run(
        "summarise this",
        make_file(tmp_path, "hello"),
        provider,
        store,
        log,
        announce=announce,
    )

    assert result.ok is True
    assert order[0] == ("announce", "grant_1", 5)
    assert order[1] == ("respond",)


def test_the_loop_runs_without_an_announce_hook(tmp_path):
    """Display is not security: no announce means no output, not no audit."""
    log = make_log(tmp_path)
    result = core.run(
        "summarise this",
        make_file(tmp_path),
        core.MockActionProvider(),
        GrantStore(),
        log,
        announce=None,
    )

    assert result.ok is True
    assert [entry["event"] for entry in records(log)] == [
        "question",
        "grant",
        "prompt",
        "provider",
        "parse",
        "grant_check",
        "execute",
    ]


class SpyStore(GrantStore):
    """A store that counts how often the session is cleared."""

    def __init__(self):
        super().__init__()
        self.clears = 0

    def clear(self):
        self.clears += 1
        super().clear()


def assert_session_is_over(store, grant_id="grant_1"):
    """The run cleared the store once, and that grant id is now dead."""
    assert store.clears == 1
    with pytest.raises(GrantError):
        store.lookup(grant_id)
    with pytest.raises(GrantError):
        store.read(grant_id)


def run_with(store, provider, tmp_path, question="summarise this", seen=None):
    """Run once, recording every announced grant id in ``seen``."""
    if seen is None:
        seen = []

    def announce(grant):
        seen.append(grant.id)

    return core.run(
        question,
        make_file(tmp_path),
        provider,
        store,
        core.NullAudit(),
        announce=announce,
    )


def test_success_ends_the_session_and_kills_the_grant(tmp_path):
    seen = []
    store = SpyStore()
    result = run_with(store, core.MockActionProvider(), tmp_path, seen=seen)

    assert result.ok is True
    assert result.output == "Summary: hello world"
    assert seen == ["grant_1"]  # it existed...
    assert_session_is_over(store)  # ...and it is dead now


def test_a_denial_ends_the_session_and_kills_the_grant(tmp_path):
    provider = ScriptedProvider('{"tool":"summarize_text","grant_id":"grant_2"}')
    seen = []
    store = SpyStore()
    result = run_with(store, provider, tmp_path, seen=seen)

    assert result.ok is False
    assert result.error == "denied: the action names a different grant"
    assert seen == ["grant_1"]
    assert_session_is_over(store)


def test_a_provider_failure_ends_the_session_and_kills_the_grant(tmp_path):
    provider = ScriptedProvider(raises=RuntimeError("boom"))
    seen = []
    store = SpyStore()
    result = run_with(store, provider, tmp_path, seen=seen)

    assert result.ok is False
    assert result.error == "the provider could not answer"
    assert seen == ["grant_1"]
    assert_session_is_over(store)


def test_a_parse_failure_ends_the_session_and_kills_the_grant(tmp_path):
    provider = ScriptedProvider("run a shell command instead")
    seen = []
    store = SpyStore()
    result = run_with(store, provider, tmp_path, seen=seen)

    assert result.ok is False
    assert "not a valid action" in result.error
    assert seen == ["grant_1"]
    assert_session_is_over(store)


def test_an_invalid_question_still_ends_the_session(tmp_path):
    store = SpyStore()
    result = run_with(store, core.MockActionProvider(), tmp_path, question="   ")

    assert result.ok is False
    assert result.error == "question is empty"
    assert store.clears == 1
    with pytest.raises(GrantError):
        store.lookup("grant_1")

"""Tests for the CLI wiring: what it shows, which provider it calls, where it logs."""

import json

import pytest

from kayt import cli, core
from kayt.grants import GrantStore
from kayt.providers.base import Provider

VALID_REPLY = '{"tool":"summarize_text","grant_id":"grant_1"}'


class RecordingProvider(Provider):
    """A provider with its own name, so the printed line can be checked."""

    name = "decoy"

    def __init__(self):
        self.prompts = []

    def respond(self, prompt):
        self.prompts.append(prompt)
        return VALID_REPLY


def make_file(tmp_path, text="some notes"):
    path = tmp_path / "notes.txt"
    path.write_text(text, encoding="utf-8")
    return path


def audit_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_header_names_the_file_its_size_and_the_provider_called(
    tmp_path, capsys, monkeypatch
):
    provider = RecordingProvider()
    monkeypatch.setattr(cli, "build_provider", lambda: provider)
    path = make_file(tmp_path)

    cli.main(["summarise this", "--file", str(path)])

    out = capsys.readouterr().out.splitlines()
    assert out == [
        f"File: notes.txt ({path.stat().st_size} bytes)",
        "Provider: decoy",
        cli.PRIVACY_NOTICE,
        "Summary: some notes",
    ]
    # The displayed name came from the provider that was really asked.
    assert provider.name == "decoy"
    assert len(provider.prompts) == 1
    assert "summarise this" in provider.prompts[0]


def test_privacy_notice_says_no_content_leaves_this_computer(tmp_path, capsys):
    cli.main(["summarise this", "--file", str(make_file(tmp_path))])

    out = capsys.readouterr().out
    assert "No content leaves this computer." in out


def test_a_question_without_a_file_fails_closed(capsys):
    with pytest.raises(SystemExit) as err:
        cli.main(["what is this?"])

    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: no file selected (pass --file PATH)\n"


def test_no_audit_path_means_no_logging(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv(cli.AUDIT_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    path = make_file(tmp_path)

    cli.main(["summarise this", "--file", str(path)])

    capsys.readouterr()
    assert sorted(item.name for item in tmp_path.iterdir()) == ["notes.txt"]
    assert isinstance(cli.build_audit(None), core.NullAudit)
    assert getattr(cli.build_audit(None), "path", None) is None


def test_the_environment_variable_selects_the_audit_log(
    tmp_path, capsys, monkeypatch
):
    log = tmp_path / "audit.jsonl"
    monkeypatch.setenv(cli.AUDIT_ENV, str(log))

    cli.main(["summarise this", "--file", str(make_file(tmp_path))])

    capsys.readouterr()
    events = [entry["event"] for entry in audit_lines(log)]
    assert events == [
        "question",
        "grant",
        "prompt",
        "provider",
        "parse",
        "grant_check",
        "execute",
    ]


def test_the_explicit_option_wins_over_the_environment(
    tmp_path, capsys, monkeypatch
):
    chosen = tmp_path / "chosen.jsonl"
    ignored = tmp_path / "ignored.jsonl"
    monkeypatch.setenv(cli.AUDIT_ENV, str(ignored))

    cli.main(
        [
            "summarise this",
            "--file",
            str(make_file(tmp_path)),
            "--audit-log",
            str(chosen),
        ]
    )

    capsys.readouterr()
    assert chosen.exists()
    assert not ignored.exists()


def test_the_default_audit_path_is_never_inside_the_source_tree(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.delenv(cli.AUDIT_ENV, raising=False)
    monkeypatch.chdir(tmp_path)

    cli.main(["summarise this", "--file", str(make_file(tmp_path))])
    capsys.readouterr()

    assert not list(tmp_path.glob("**/*.jsonl"))
    assert cli.build_parser().parse_args(["q", "--file", "x.txt"]).audit_log is None


def test_an_unwritable_audit_log_warns_once_at_exit(
    tmp_path, capsys, monkeypatch
):
    provider = RecordingProvider()
    monkeypatch.setattr(cli, "build_provider", lambda: provider)
    missing_dir = tmp_path / "absent" / "audit.jsonl"

    cli.main(
        [
            "summarise this",
            "--file",
            str(make_file(tmp_path)),
            "--audit-log",
            str(missing_dir),
        ]
    )

    captured = capsys.readouterr()
    assert "Summary: some notes" in captured.out
    assert captured.err.count("\n") == 1
    assert captured.err.startswith("warning: ")
    assert "audit event(s) could not be written" in captured.err


def test_a_garbage_reply_is_one_error_line_after_the_header(
    tmp_path, capsys, monkeypatch
):
    provider = RecordingProvider()
    provider.respond = lambda prompt: "run the shell instead"
    monkeypatch.setattr(cli, "build_provider", lambda: provider)

    with pytest.raises(SystemExit) as err:
        cli.main(["summarise this", "--file", str(make_file(tmp_path))])

    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.count("\n") == 1
    assert captured.err.startswith("error: ")
    assert "not a valid action" in captured.err
    assert "shell" not in captured.err
    assert captured.out.splitlines() == [
        "File: notes.txt (10 bytes)",
        "Provider: decoy",
        cli.PRIVACY_NOTICE,
    ]


def test_the_provider_name_printed_is_the_one_the_core_reports(
    tmp_path, capsys, monkeypatch
):
    provider = RecordingProvider()
    monkeypatch.setattr(cli, "build_provider", lambda: provider)

    result = core.run(
        "summarise this",
        make_file(tmp_path),
        cli.build_provider(),
        GrantStore(),
        core.NullAudit(),
    )

    assert result.provider == provider.name == "decoy"
    assert len(provider.prompts) == 1
    assert capsys.readouterr().out == ""

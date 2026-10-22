"""End-to-end CLI tests: run the real ``python -m kayt.cli`` in a subprocess.

Every other CLI test calls ``cli.main`` in-process, which cannot catch import,
argument-parsing or packaging mistakes. These tests start a fresh interpreter
from a temporary working directory and assert on real exit codes and streams.

The ``subprocess`` import here is deliberate and allowed: the adversarial guard
in ``tests/test_adversarial.py`` scans ``src/kayt`` only, and the last test in
this file pins that boundary.
"""

import os
import subprocess
import sys
from pathlib import Path

import kayt

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
PRIVACY_NOTICE = "KAYT reads only this file. No content leaves this computer."
OVERSIZED_BYTES = 100 * 1024 + 1


def run_cli(tmp_path, *args):
    """Run the module from ``tmp_path`` with no install required."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    env.pop("KAYT_AUDIT_LOG", None)
    return subprocess.run(
        [sys.executable, "-m", "kayt.cli", *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def assert_failed(result):
    """A refused run: exit 1, empty stdout, exactly one error line."""
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.count("\n") == 1
    assert result.stderr.startswith("error: ")
    assert "Traceback" not in result.stderr


def test_valid_file_runs_from_an_unrelated_directory(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("hello from the process test", encoding="utf-8")

    result = run_cli(tmp_path, "summarise this", "--file", "notes.txt")

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"File: notes.txt ({notes.stat().st_size} bytes)",
        "Provider: mock",
        PRIVACY_NOTICE,
        "Summary: hello from the process test",
    ]


def test_oversized_file_is_refused(tmp_path):
    (tmp_path / "big.txt").write_bytes(b"a" * OVERSIZED_BYTES)

    result = run_cli(tmp_path, "summarise this", "--file", "big.txt")

    assert_failed(result)
    assert "too large" in result.stderr


def test_unsupported_extension_is_refused(tmp_path):
    (tmp_path / "notes.pdf").write_text("some text", encoding="utf-8")

    result = run_cli(tmp_path, "summarise this", "--file", "notes.pdf")

    assert_failed(result)
    assert "unsupported file type" in result.stderr


def test_missing_file_is_refused(tmp_path):
    result = run_cli(tmp_path, "summarise this", "--file", "absent.txt")

    assert_failed(result)
    assert "file not found" in result.stderr


def test_omitting_the_file_option_fails_closed(tmp_path):
    result = run_cli(tmp_path, "what is this?")

    assert_failed(result)
    assert "--file" in result.stderr


def test_the_import_guard_scans_only_the_package():
    """This file imports subprocess; the guard must never scan tests/."""
    package = Path(kayt.__file__).resolve().parent
    this_file = Path(__file__).resolve()

    assert package == SRC / "kayt"
    assert not this_file.is_relative_to(package)
    assert "import subprocess" in this_file.read_text(encoding="utf-8")

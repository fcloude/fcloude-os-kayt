# FCLOUDE OS + KAYT
KAYT is a transparent, default-deny assistant that reads only the file the user
picked, explains what it will do, and cannot do anything else.

## Status

Early prototype (Goal 4 in progress). The CLI runs the full chain end to end -- question,
grant, prompt, provider, schema validation, grant-id check, policy-checked tool,
audit -- but only with a mock provider that ignores the prompt and returns a
fixed action. The output is a deterministic prefix of the selected file,
labelled `Summary:`, not a model-written summary. **Nothing has been measured
against a real model**: prompt-injection behaviour and summary quality are
unknown. The package contains no network or shell code, and model text can only
name a grant id, never a path. Passing tests are evidence, not a security
certification; see `docs/security-test-report.md` and
`docs/mvp-acceptance.md`.

## Setup

Requires Python 3.11 or newer. From the repository root:

Windows (Git Bash or PowerShell):

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

POSIX:

```
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

`.[dev]` adds pytest. If you would rather not install the package, skip the pip
step and use the `PYTHONPATH=src` form shown below; pytest also works without an
install because `pyproject.toml` puts `src` on its path.

## Run

```
.venv/Scripts/python.exe -m kayt.cli "summarise this" --file notes.txt
```

Install-free equivalent, from the repository root:

```
PYTHONPATH=src .venv/Scripts/python.exe -m kayt.cli "summarise this" --file notes.txt
```

There is no console script yet (deferred to Goal 6), so the entry point is
`python -m kayt.cli`. The file must be `.txt` or `.md`, non-empty, valid UTF-8,
at most 100 KB, and not a symlink. `--file` is required: without it the command
exits 1 with a single error line. Before processing, KAYT prints the file name
and size, the provider, and a line saying no content leaves the computer.

Optional audit log (off by default, and never written inside the source tree):

```
.venv/Scripts/python.exe -m kayt.cli "summarise this" --file notes.txt --audit-log audit.jsonl
```

Or set `KAYT_AUDIT_LOG` instead of `--audit-log`. One JSON line is written per
step; file content is never logged, and an unwritable path only produces a
one-line warning at exit.

## Tests

```
.venv/Scripts/python.exe -m pytest -q -rs
```

POSIX: `.venv/bin/python -m pytest -q -rs`.

# KAYT MVP acceptance checklist (Goal 4, Milestone 4.3)

Audit of the tests that exist today against the Milestone 4.3 checklist and the
Master Blueprint P0 items. Written 2026-10-22 on Windows 11 (10.0.26300),
Python 3.13.14. This document adds no tests; it records what is and is not
proven, and lists the gaps to close.

**Strictness rule used below:** a test counts as **covered** only when it
asserts the acceptance behaviour itself. If it only proves a piece indirectly —
for example, a component-level check with no assertion on what the application
does with it — the item is **partial**.

## Suite as run

```
.venv/Scripts/python.exe -m pytest -q -rs
144 passed, 0 skipped
```

Exit status 0, no test skipped. 13 test files under `tests/`, including
`tests/test_cli_process.py`, which runs the real `python -m kayt.cli` in a
subprocess from a temporary working directory.

## Milestone 4.3 checklist

| Item | Test name(s) with file | Status | Note |
|---|---|---|---|
| Normal summary request | `test_happy_path_runs_every_step_once_in_order` — `tests/test_core.py`<br>`test_file_option_reports_filename` — `tests/test_cli.py`<br>`test_header_names_the_file_its_size_and_the_provider_called` — `tests/test_cli_wiring.py`<br>`test_cli_runs` — `tests/test_smoke.py`<br>`test_valid_file_runs_from_an_unrelated_directory` — `tests/test_cli_process.py` | **covered** | Core test pins the exact output (`Summary: hello world`) and the seven audited steps; CLI tests pin the printed header, the privacy line and the summary line; the subprocess test runs the real module from an unrelated directory and asserts those four output lines plus exit 0 and empty stderr. |
| Explanation request | `test_the_prompt_carries_the_question_the_file_text_and_the_grant_id` — `tests/test_core.py` | **partial** | Only proves the question text reaches the prompt. The mock ignores the prompt and always returns the summary action, so an explanation request is indistinguishable from a summary request and no explanation output exists to assert. See the note below the table. |
| File too large | `test_oversized_file_rejected` — `tests/test_grants.py`<br>`test_file_growing_past_limit_is_rejected` — `tests/test_grants.py`<br>`test_file_at_size_limit_accepted` — `tests/test_grants.py`<br>`test_oversized_file_is_refused` — `tests/test_cli_process.py` | **covered** | The 100 KB limit is pinned at its boundary (rejected at 102,401 bytes, accepted at 102,400, re-checked when the file grows during the read), and the subprocess test feeds a 102,401-byte file to the real CLI: exit 1, empty stdout, one `error:` line mentioning `too large`, no traceback. |
| Unsupported file | `test_wrong_extension_rejected` — `tests/test_grants.py`<br>`test_directory_rejected` — `tests/test_grants.py`<br>`test_unsupported_extension_is_refused` — `tests/test_cli_process.py` | **covered** | `.pdf` is refused at the grant layer and, through the real CLI, as exit 1 with empty stdout, one `error:` line mentioning `unsupported file type`, and no traceback. Directories are refused by the regular-file branch (grant layer only). |
| Missing or unreadable file | `test_missing_file_rejected` — `tests/test_grants.py`<br>`test_cli_failure_is_one_line_and_exits_nonzero` — `tests/test_inputs.py`<br>`test_a_bad_file_stops_before_the_provider_is_asked` — `tests/test_core.py`<br>`test_missing_file_is_refused` — `tests/test_cli_process.py`<br>`test_non_utf8_file_rejected` — `tests/test_grants.py`<br>`test_unexpected_error_fails_closed_and_stores_no_grant` — `tests/test_grants.py` | **partial** | A missing file is covered end to end, including through the real CLI (exit 1, one `error:` line, no provider call, no traceback). Undecodable bytes and unexpected read errors fail closed. An OS permission-denied file is **not** exercised; `docs/decisions.md` records that branch as untested on Windows. |
| Malformed provider output | `test_a_provider_returning_garbage_is_refused_before_execution` — `tests/test_core.py`<br>`test_a_garbage_reply_is_one_error_line_after_the_header` — `tests/test_cli_wiring.py`<br>`tests/test_schema.py` (whole file)<br>`test_malformed_or_truncated_json_is_refused` — `tests/test_adversarial.py` | **covered** | Refused before execution, one fixed error line, raw reply never echoed, no fallback action. Schema tests cover truncated JSON, extra/missing fields, wrong types, duplicate keys, non-objects and oversized replies. |
| Denied tool request | `test_a_denied_action_stops_without_output_and_is_audited` — `tests/test_core.py`<br>`test_tool_outside_policy_allowlist_denied` — `tests/test_policy.py`<br>`test_tool_outside_policy_allowlist_denied` — `tests/test_tools.py`<br>`test_grant_cleared_between_callers_check_and_execute` — `tests/test_tools.py`<br>`test_unknown_tool_run_shell_is_refused` — `tests/test_adversarial.py`<br>`test_invented_grant_99_is_refused` — `tests/test_adversarial.py` | **covered** | Denial lands in the audit log, output is empty, the reason is a fixed string, and the gateway re-checks policy at execution time so a stale allow cannot be replayed. |
| Session clearing and grant expiration | `test_success_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_a_denial_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_a_provider_failure_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_a_parse_failure_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_an_invalid_question_still_ends_the_session` — `tests/test_core.py`<br>`test_previously_valid_id_is_dead_after_clear` — `tests/test_grants.py`<br>`test_ids_are_not_reused_after_clear` — `tests/test_grants.py`<br>`test_expired_grant_after_clear_is_refused` — `tests/test_adversarial.py` | **covered** | `run` clears the store exactly once on success and on each covered failure path (denial, provider failure, parse failure, invalid question); the `finally` covers the remaining returns by construction. The announced id is dead afterwards, a cleared id is never reused, and an expired grant is denied at execution. |
| Displayed provider matches the provider called | `test_header_names_the_file_its_size_and_the_provider_called` — `tests/test_cli_wiring.py`<br>`test_the_provider_name_printed_is_the_one_the_core_reports` — `tests/test_cli_wiring.py` | **covered** | The test injects a provider whose name is `decoy`, so a hard-coded `Provider: mock` line would fail; the printed name and the provider that received the prompt are checked together. |
| Runs from documented instructions | `test_valid_file_runs_from_an_unrelated_directory` — `tests/test_cli_process.py`<br>`test_oversized_file_is_refused` — `tests/test_cli_process.py`<br>`test_unsupported_extension_is_refused` — `tests/test_cli_process.py`<br>`test_missing_file_is_refused` — `tests/test_cli_process.py`<br>`test_omitting_the_file_option_fails_closed` — `tests/test_cli_process.py` | **covered** | `README.md` now documents setup, the `python -m kayt.cli ... --file ...` command, the install-free `PYTHONPATH=src` form, the audit-log option and the test command. The subprocess tests execute the documented module entry point with `sys.executable` and `PYTHONPATH=src` from a temporary cwd, so the install-free path is exercised as written. There is still no console script (deferred to Goal 6), so the documented entry point is `python -m`. |

**On "explanation request":** it cannot be distinguished from "summary" in this
build. MockActionProvider ignores the prompt and always returns
`{"tool":"summarize_text","grant_id":"grant_1"}`, and `summarize_text` returns a
fixed prefix of the file. The question is forwarded into the prompt, and that is
all a test can currently prove; no assertion can tell an explanation request
from a summary request, and no explanation output exists.

## Master Blueprint P0 items

| Item | Test name(s) with file | Status | Note |
|---|---|---|---|
| Text input/output | `test_empty_question_rejected` — `tests/test_inputs.py`<br>`test_whitespace_only_question_rejected` — `tests/test_inputs.py`<br>`test_file_option_reports_filename` — `tests/test_cli.py`<br>`test_cli_runs` — `tests/test_smoke.py` | **covered** | A question is required, whitespace-only input is refused, and the result and errors are printed as text. Typed-only mode was dropped by decision, so text input exists as the question that accompanies a selected file. |
| Selected-file input | `tests/test_grants.py` (create, size, extension, symlink, snapshot reads)<br>`test_file_option_reports_filename` — `tests/test_cli.py`<br>`test_a_bad_file_stops_before_the_provider_is_asked` — `tests/test_core.py` | **covered** | Grants are created from a caller-supplied path and validated before any provider call; the model's output can only name a grant id, never a path (see the permission allowlist rows). |
| Provider adapter | `test_mock_provider_returns_predictable_response` — `tests/test_mock_provider.py`<br>`test_mock_provider_reports_its_name` — `tests/test_mock_provider.py`<br>`test_mock_action_provider_returns_the_fixed_action` — `tests/test_core.py`<br>`test_header_names_the_file_its_size_and_the_provider_called` — `tests/test_cli_wiring.py` | **covered** | Three `Provider` implementations exercise the same `respond`/`name` interface, and core/CLI call it only through that interface. Nothing enforces the ABC at runtime (duck typing), which is listed as a gap rather than treated as proven. |
| Input limits and errors | `test_oversized_file_rejected` — `tests/test_grants.py`<br>`test_oversized_file_is_refused` — `tests/test_cli_process.py`<br>`test_unsupported_extension_is_refused` — `tests/test_cli_process.py`<br>`test_missing_file_is_refused` — `tests/test_cli_process.py`<br>`test_oversized_input_rejected_before_parsing` — `tests/test_schema.py`<br>`test_cli_failure_is_one_line_and_exits_nonzero` — `tests/test_inputs.py`<br>`test_empty_file_is_rejected_with_one_line_error` — `tests/test_cli.py`<br>`test_a_refusal_with_control_characters_stays_on_one_line` — `tests/test_core.py` | **partial** | File size, unsupported type and missing file are now asserted end to end through the real CLI (exit 1, empty stdout, one `error:` line, no traceback); raw-output size is capped in the schema and refusals with newlines or escape bytes stay on one line. The only remaining untested input error is OS permission-denied (see gaps), so the item stays partial. |
| Permission allowlist | `test_tool_outside_policy_allowlist_denied` — `tests/test_policy.py`<br>`test_policy_allowlist_is_separate_from_schemas` — `tests/test_policy.py`<br>`test_unknown_tool_rejected_without_echo` — `tests/test_schema.py`<br>`test_tool_outside_policy_allowlist_denied` — `tests/test_tools.py`<br>`test_unknown_tool_run_shell_is_refused` — `tests/test_adversarial.py` | **covered** | Schema and policy keep independent allowlists; an unknown tool is refused by both; there is no override and no dynamic dispatch. |

## Gaps to close

No tests were added for these; they are the next work.

1. **Explanation request has no distinct behaviour.** Needs a provider whose
   output depends on the question (or a second allowlisted tool) before the
   item can move from partial to covered.
2. **Permission-denied (OS-level unreadable) file is untested.** The branch
   exists in `grants.py`; `docs/decisions.md` records it as unverified because
   the development host is Windows. This is the only input error without a
   test, and it keeps the Blueprint "input limits and errors" item partial.
3. **The provider boundary is convention, not enforcement.** No test asserts
   that `core.run` refuses an object that does not implement the `Provider`
   interface; it uses `respond` and `name` by duck typing.
4. **Session clearing is not audited.** Behaviour is covered, but `clear()`
   writes no event, so a failed or skipped clear would leave no trace in the
   log.
5. **The editable-install path in `README.md` has no regression test.** The
   subprocess tests use the documented `PYTHONPATH=src` form; the
   `pip install -e ".[dev]"` step was run by hand on 2026-10-22 (in the
   existing `.venv`) but is not exercised by the suite.

## How to run

Environment used for these counts: Windows 11 (10.0.26300), Python 3.13.14,
standard library plus pytest 9.1.1. The suite needs no package install —
`pyproject.toml` puts `src` on pytest's path. `README.md` documents both the
editable install and the install-free form; the pip step below was executed on
2026-10-22 against the existing `.venv` (the `python -m venv` line was not,
because the virtualenv already existed).

```bash
# optional setup, as documented in README.md
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"

# full suite (verified 2026-10-22: 144 passed, 0 skipped, exit 0)
.venv/Scripts/python.exe -m pytest -q -rs

# one file only
.venv/Scripts/python.exe -m pytest -q -rs tests/test_cli_process.py

# the app on one selected file (installed package)
.venv/Scripts/python.exe -m kayt.cli "summarise this" --file notes.txt

# the install-free form, also used by tests/test_cli_process.py
PYTHONPATH=src .venv/Scripts/python.exe -m kayt.cli "summarise this" --file notes.txt
```

The equivalent POSIX paths are `.venv/bin/python -m pytest -q -rs` and
`.venv/bin/python -m kayt.cli ...`; only the Windows commands above were
executed for this document.

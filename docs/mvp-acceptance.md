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
138 passed, 0 skipped
```

Exit status 0, no test skipped. 12 test files under `tests/`.

## Milestone 4.3 checklist

| Item | Test name(s) with file | Status | Note |
|---|---|---|---|
| Normal summary request | `test_happy_path_runs_every_step_once_in_order` — `tests/test_core.py`<br>`test_file_option_reports_filename` — `tests/test_cli.py`<br>`test_header_names_the_file_its_size_and_the_provider_called` — `tests/test_cli_wiring.py`<br>`test_cli_runs` — `tests/test_smoke.py` | **covered** | Core test pins the exact output (`Summary: hello world`) and the seven audited steps; CLI tests pin the printed header, the privacy line and the summary line. |
| Explanation request | `test_the_prompt_carries_the_question_the_file_text_and_the_grant_id` — `tests/test_core.py` | **partial** | Only proves the question text reaches the prompt. The mock ignores the prompt and always returns the summary action, so an explanation request is indistinguishable from a summary request and no explanation output exists to assert. See the note below the table. |
| File too large | `test_oversized_file_rejected` — `tests/test_grants.py`<br>`test_file_growing_past_limit_is_rejected` — `tests/test_grants.py`<br>`test_file_at_size_limit_accepted` — `tests/test_grants.py` | **partial** | The 100 KB limit is enforced and its boundary pinned (rejected at 102,401 bytes, accepted at 102,400, re-checked when the file grows during the read), but only at the grant layer. Nothing feeds an oversized file through `core.run` or the CLI, so the application's rejection path and its one-line error are unproven (see gaps). |
| Unsupported file | `test_wrong_extension_rejected` — `tests/test_grants.py`<br>`test_directory_rejected` — `tests/test_grants.py` | **partial** | `.pdf` is refused as an unsupported type and a directory by the regular-file branch, but only at the grant layer. No test drives an unsupported file through `core.run` or the CLI, so the application's output for it is inferred (see gaps). |
| Missing or unreadable file | `test_missing_file_rejected` — `tests/test_grants.py`<br>`test_cli_failure_is_one_line_and_exits_nonzero` — `tests/test_inputs.py`<br>`test_a_bad_file_stops_before_the_provider_is_asked` — `tests/test_core.py`<br>`test_non_utf8_file_rejected` — `tests/test_grants.py`<br>`test_unexpected_error_fails_closed_and_stores_no_grant` — `tests/test_grants.py` | **partial** | Missing file is covered end to end (exit 1, one `error:` line, no provider call). Undecodable bytes and unexpected read errors fail closed. An OS permission-denied file is **not** exercised; `docs/decisions.md` already records that branch as untested on Windows. |
| Malformed provider output | `test_a_provider_returning_garbage_is_refused_before_execution` — `tests/test_core.py`<br>`test_a_garbage_reply_is_one_error_line_after_the_header` — `tests/test_cli_wiring.py`<br>`tests/test_schema.py` (whole file)<br>`test_malformed_or_truncated_json_is_refused` — `tests/test_adversarial.py` | **covered** | Refused before execution, one fixed error line, raw reply never echoed, no fallback action. Schema tests cover truncated JSON, extra/missing fields, wrong types, duplicate keys, non-objects and oversized replies. |
| Denied tool request | `test_a_denied_action_stops_without_output_and_is_audited` — `tests/test_core.py`<br>`test_tool_outside_policy_allowlist_denied` — `tests/test_policy.py`<br>`test_tool_outside_policy_allowlist_denied` — `tests/test_tools.py`<br>`test_grant_cleared_between_callers_check_and_execute` — `tests/test_tools.py`<br>`test_unknown_tool_run_shell_is_refused` — `tests/test_adversarial.py`<br>`test_invented_grant_99_is_refused` — `tests/test_adversarial.py` | **covered** | Denial lands in the audit log, output is empty, the reason is a fixed string, and the gateway re-checks policy at execution time so a stale allow cannot be replayed. |
| Session clearing and grant expiration | `test_success_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_a_denial_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_a_provider_failure_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_a_parse_failure_ends_the_session_and_kills_the_grant` — `tests/test_core.py`<br>`test_an_invalid_question_still_ends_the_session` — `tests/test_core.py`<br>`test_previously_valid_id_is_dead_after_clear` — `tests/test_grants.py`<br>`test_ids_are_not_reused_after_clear` — `tests/test_grants.py`<br>`test_expired_grant_after_clear_is_refused` — `tests/test_adversarial.py` | **covered** | `run` clears the store exactly once on success and on each covered failure path (denial, provider failure, parse failure, invalid question); the `finally` covers the remaining returns by construction. The announced id is dead afterwards, a cleared id is never reused, and an expired grant is denied at execution. |
| Displayed provider matches the provider called | `test_header_names_the_file_its_size_and_the_provider_called` — `tests/test_cli_wiring.py`<br>`test_the_provider_name_printed_is_the_one_the_core_reports` — `tests/test_cli_wiring.py` | **covered** | The test injects a provider whose name is `decoy`, so a hard-coded `Provider: mock` line would fail; the printed name and the provider that received the prompt are checked together. |
| Runs from documented instructions | — | **not covered** | No test invokes the documented command line; every CLI test calls `cli.main(...)` in-process. `README.md` contains no install or run instructions, and `pyproject.toml` defines no console script, so there are no "documented instructions" to test yet. The commands in *How to run* were executed by hand, which is not a test. |

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
| Input limits and errors | `test_oversized_file_rejected` — `tests/test_grants.py`<br>`test_file_at_size_limit_accepted` — `tests/test_grants.py`<br>`test_oversized_input_rejected_before_parsing` — `tests/test_schema.py`<br>`test_cli_failure_is_one_line_and_exits_nonzero` — `tests/test_inputs.py`<br>`test_empty_file_is_rejected_with_one_line_error` — `tests/test_cli.py`<br>`test_a_refusal_with_control_characters_stays_on_one_line` — `tests/test_core.py` | **partial** | An empty question is refused by the input check (asserted in `core.run`), an empty file is refused through the CLI with one `error:` line, raw-output size is capped in the schema, and refusals with newlines or escape bytes stay on one line. The file-size limit is asserted only in its enforcing module, never through `core.run` or the CLI, and permission-denied is untested (see gaps). |
| Permission allowlist | `test_tool_outside_policy_allowlist_denied` — `tests/test_policy.py`<br>`test_policy_allowlist_is_separate_from_schemas` — `tests/test_policy.py`<br>`test_unknown_tool_rejected_without_echo` — `tests/test_schema.py`<br>`test_tool_outside_policy_allowlist_denied` — `tests/test_tools.py`<br>`test_unknown_tool_run_shell_is_refused` — `tests/test_adversarial.py` | **covered** | Schema and policy keep independent allowlists; an unknown tool is refused by both; there is no override and no dynamic dispatch. |

## Gaps to close

No tests were added for these; they are the next work.

1. **Explanation request has no distinct behaviour.** Needs a provider whose
   output depends on the question (or a second allowlisted tool) before the
   item can move from partial to covered.
2. **No test runs the app the way a user would.** Every CLI test calls
   `cli.main()` in-process; nothing exercises `python -m kayt.cli` as a
   subprocess, and there is no console-script entry point. A test would also
   catch import and packaging errors that in-process calls hide.
3. **`README.md` documents no install or run steps.** The "runs from documented
   instructions" item cannot be tested until the instructions exist and
   `pyproject.toml` exposes a command.
4. **Permission-denied (OS-level unreadable) file is untested.** The branch
   exists in `grants.py`; `docs/decisions.md` records it as unverified because
   the development host is Windows.
5. **Too-large and unsupported-type rejections are only asserted at the grant
   layer.** No test checks the CLI's single `error:` line for either case, so
   the user-facing behaviour for these two is inferred rather than proven.
6. **The provider boundary is convention, not enforcement.** No test asserts
   that `core.run` refuses an object that does not implement the `Provider`
   interface; it uses `respond` and `name` by duck typing.
7. **Session clearing is not audited.** Behaviour is covered, but `clear()`
   writes no event, so a failed or skipped clear would leave no trace in the
   log.

## How to run

Environment used for these counts: Windows 11 (10.0.26300), Python 3.13.14,
standard library plus pytest 9.1.1. No package install step is needed —
`pyproject.toml` puts `src` on the path for pytest.

```bash
# full suite (verified 2026-10-22: 138 passed, 0 skipped, exit 0)
.venv/Scripts/python.exe -m pytest -q -rs

# one file only
.venv/Scripts/python.exe -m pytest -q -rs tests/test_cli_wiring.py

# the app on one selected file
PYTHONPATH=src .venv/Scripts/python.exe -m kayt.cli "summarise this" --file notes.txt
```

The equivalent POSIX paths are `.venv/bin/python -m pytest -q -rs` and
`PYTHONPATH=src .venv/bin/python -m kayt.cli ...`; only the Windows commands
above were executed for this document.

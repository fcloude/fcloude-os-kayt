"""KAYT command-line entry point.

The CLI is display and wiring only: it never decides a security question. It
resolves the audit destination (an explicit ``--audit-log`` or
``KAYT_AUDIT_LOG``; otherwise logging is off, and never a path inside the
source tree), announces what will be read, then hands the question and file to
``core.run`` and prints what came back.
"""

import argparse
import os
import sys

from kayt import core
from kayt.audit import AuditLog
from kayt.grants import Grant, GrantStore

AUDIT_ENV = "KAYT_AUDIT_LOG"
PRIVACY_NOTICE = "KAYT reads only this file. No content leaves this computer."


def build_parser() -> argparse.ArgumentParser:
    """Describe the command line: a question, a file, and an audit option."""
    parser = argparse.ArgumentParser(prog="kayt")
    parser.add_argument("question", help="the question to ask")
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="the .txt or .md file to read (required)",
    )
    parser.add_argument(
        "--audit-log",
        metavar="PATH",
        default=None,
        help=(
            "write one JSON-lines audit record per step to PATH "
            f"(env: {AUDIT_ENV}; default: no logging)"
        ),
    )
    return parser


def build_provider() -> core.MockActionProvider:
    """Return the provider this build actually calls."""
    return core.MockActionProvider()


def build_audit(path: str | None) -> object:
    """Resolve the audit destination: explicit, then env, else no logging."""
    chosen = path or os.environ.get(AUDIT_ENV)
    if not chosen:
        return core.NullAudit()
    return AuditLog(chosen)


def print_header(grant: Grant, provider: object) -> None:
    """Say what will be read and which provider answers, before asking it."""
    print(f"File: {grant.path.name} ({grant.size} bytes)")
    print(f"Provider: {getattr(provider, 'name', 'unknown')}")
    print(PRIVACY_NOTICE)


def warn_about_audit(audit: object) -> None:
    """Print one line when audit records could not be written."""
    failures = getattr(audit, "failures", 0)
    if failures:
        print(
            f"warning: {failures} audit event(s) could not be written",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> None:
    """Run one question against one chosen file, then exit."""
    args = build_parser().parse_args(argv)
    provider = build_provider()
    audit = build_audit(args.audit_log)

    exit_code = 0
    try:
        if not args.file:
            print(
                "error: no file selected (pass --file PATH)",
                file=sys.stderr,
            )
            exit_code = 1
        else:
            result = core.run(
                args.question,
                args.file,
                provider,
                GrantStore(),
                audit,
                announce=lambda grant: print_header(grant, provider),
            )
            if result.ok:
                print(result.output)
            else:
                print(f"error: {result.error}", file=sys.stderr)
                exit_code = 1
    finally:
        warn_about_audit(audit)

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()

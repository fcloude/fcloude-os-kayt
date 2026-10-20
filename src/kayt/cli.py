"""KAYT command-line entry point."""

import argparse
import sys

from kayt.inputs import InputError, check_question, read_file
from kayt.providers.mock import MockProvider


def build_parser() -> argparse.ArgumentParser:
    """Describe the command line: a question, plus an optional file."""
    parser = argparse.ArgumentParser(prog="kayt")
    parser.add_argument("question", help="the question to ask")
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="use this file as the input instead of typed text",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Check the input, report which one is used, then print a response."""
    args = build_parser().parse_args(argv)
    provider = MockProvider()

    try:
        question = check_question(args.question)
        source = read_file(args.file) if args.file else question
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None

    if args.file:
        print(f"Input: file {args.file}")
    else:
        print("Input: typed text")

    print(f"Provider: {provider.name}")
    print(provider.respond(source))


if __name__ == "__main__":
    main()

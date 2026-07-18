"""Command-line interface for the Sola interpreter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sola.errors import SolaError
from sola.interpreter import Interpreter
from sola.lexer import Lexer
from sola.parser import Parser


def run_file(path: Path, step_limit: int = 100_000) -> int:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[IOError] {path}: {exc}", file=sys.stderr)
        return 1

    return run_source(source, filename=str(path), step_limit=step_limit)


def run_source(source: str, filename: str = "<stdin>", step_limit: int = 100_000) -> int:
    try:
        tokens = Lexer(source, filename).tokenize()
        program = Parser(tokens, filename).parse()
        Interpreter(filename=filename, step_limit=step_limit).interpret(program)
        return 0
    except SolaError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sola",
        description="Run Sola source files.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Path to a .sola source file",
    )
    parser.add_argument(
        "--step-limit",
        type=int,
        default=100_000,
        help="Maximum number of execution steps before aborting (default: 100000)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)

    if args_list and args_list[0] == "run":
        run_parser = argparse.ArgumentParser(prog="sola run")
        run_parser.add_argument("file", type=Path, help="Path to a .sola source file")
        run_parser.add_argument(
            "--step-limit",
            type=int,
            default=100_000,
            help="Maximum number of execution steps before aborting (default: 100000)",
        )
        args = run_parser.parse_args(args_list[1:])
        return run_file(args.file, step_limit=args.step_limit)

    parser = build_parser()
    args = parser.parse_args(args_list)

    if args.file is not None:
        return run_file(args.file, step_limit=args.step_limit)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

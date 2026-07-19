"""Command-line interface for the Simo language toolchain."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from simo.devserver import serve
from simo.errors import SimoError
from simo.formatter import format_source
from simo.interpreter import Interpreter
from simo.project import create_project, load_project, resolve_entry
from simo.source import load_program, parse_source
from simo.testing import run_tests
from simo.web import build as build_target


COMMANDS = {"run", "check", "build", "dev", "new", "fmt", "test", "doctor"}


def run_source(
    source: str,
    filename: str = "<stdin>",
    step_limit: int = 100_000,
    output_stream=None,
) -> int:
    try:
        program = parse_source(source, filename)
        Interpreter(
            filename=filename,
            step_limit=step_limit,
            output_stream=output_stream,
        ).interpret(program)
        return 0
    except SimoError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def run_file(path: Path, step_limit: int = 100_000) -> int:
    path = path.resolve()
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[IOError] {path}: {exc}", file=sys.stderr)
        return 1
    return run_source(source, str(path), step_limit)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simo",
        description="Run, check, build, and serve Simo programs.",
    )
    parser.add_argument("--version", action="version", version="Simo 0.5.0")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="Run a console Simo program")
    run.add_argument("file", nargs="?", type=Path)
    run.add_argument("--step-limit", type=int, default=100_000)

    check = subparsers.add_parser("check", help="Parse and validate a project")
    check.add_argument("file", nargs="?", type=Path)

    build = subparsers.add_parser("build", help="Build a page for web, app, or desktop")
    build.add_argument("file", nargs="?", type=Path)
    build.add_argument("--target", choices=["web", "app", "desktop"])
    build.add_argument("--output", "-o", type=Path)

    dev = subparsers.add_parser("dev", help="Build and serve a page locally")
    dev.add_argument("file", nargs="?", type=Path)
    dev.add_argument("--target", choices=["web", "app"], default="web")
    dev.add_argument("--output", type=Path, default=Path(".simo-dev"))
    dev.add_argument("--host", default="127.0.0.1")
    dev.add_argument("--port", type=int, default=8000)
    dev.add_argument("--no-open", action="store_true")

    new = subparsers.add_parser("new", help="Create a Simo project")
    new.add_argument("name", type=Path)
    new.add_argument("--template", choices=["console", "web", "app"], default="console")

    fmt = subparsers.add_parser("fmt", help="Format Simo source files")
    fmt.add_argument("files", nargs="+", type=Path)
    fmt.add_argument("--check", action="store_true")

    test = subparsers.add_parser("test", help="Run test_*.simo files")
    test.add_argument("path", nargs="?", type=Path, default=Path("tests"))
    test.add_argument("--step-limit", type=int, default=100_000)

    subparsers.add_parser("doctor", help="Show toolchain and project information")
    return parser


def _resolve_build_settings(file: Path | None, target: str | None, output: Path | None):
    project = load_project(file or Path.cwd())
    source = resolve_entry(file)
    selected_target = target or (project.target if project.target != "console" else "web")
    selected_output = (output.resolve() if output else project.output.resolve())
    return project, source, selected_target, selected_output


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] not in COMMANDS and not arguments[0].startswith("-"):
        arguments.insert(0, "run")

    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "run":
            return run_file(resolve_entry(args.file), args.step_limit)

        if args.command == "check":
            source = resolve_entry(args.file)
            program = load_program(source)
            page_count = sum(1 for statement in program.statements if statement.__class__.__name__ == "PageDecl")
            print(f"OK {source} ({len(program.statements)} top-level statements, {page_count} page)")
            return 0

        if args.command == "build":
            _, source, target, output = _resolve_build_settings(args.file, args.target, args.output)
            result = build_target(source, output, target)
            print(f"Built {target}: {result}")
            if target == "app":
                print("The output is an installable Progressive Web App. Serve it over HTTPS to install it.")
            if target == "desktop":
                print("A Tauri 2 scaffold was generated in dist/src-tauri; see DESKTOP.md.")
            return 0

        if args.command == "dev":
            source = resolve_entry(args.file)
            serve(
                source,
                args.output,
                target=args.target,
                host=args.host,
                port=args.port,
                open_browser=not args.no_open,
            )
            return 0

        if args.command == "new":
            project = create_project(args.name, args.template)
            print(f"Created {args.template} project at {project.root}")
            print(f"Next: cd {project.root.name}")
            print("Then: simo run" if args.template == "console" else "Then: simo dev")
            return 0

        if args.command == "fmt":
            changed = 0
            for file in args.files:
                source = file.read_text(encoding="utf-8")
                formatted = format_source(source, str(file))
                if formatted != source:
                    changed += 1
                    if not args.check:
                        file.write_text(formatted, encoding="utf-8")
                        print(f"Formatted {file}")
                    else:
                        print(f"Needs formatting: {file}")
            return 1 if args.check and changed else 0

        if args.command == "test":
            _, failed = run_tests(args.path, args.step_limit)
            return 1 if failed else 0

        if args.command == "doctor":
            project = load_project()
            print("Simo 0.5.0")
            print(f"Python: {sys.version.split()[0]}")
            print(f"Project root: {project.root}")
            print(f"Entry: {project.entry}")
            print(f"Target: {project.target}")
            print(f"Output: {project.output}")
            return 0
    except SimoError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"[IOError] {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

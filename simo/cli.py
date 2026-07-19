"""Command-line interface for the Simo language toolchain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from simo.desktop import run_desktop, tkinter_available
from simo.desktop_build import build_desktop, pyinstaller_available
from simo.devserver import serve
from simo.errors import SimoError
from simo.formatter import format_source
from simo.interpreter import Interpreter
from simo.project import create_project, load_project, resolve_entry
from simo.source import load_program, parse_source
from simo.testing import run_tests
from simo.web import build as build_web_target


COMMANDS = {"run", "check", "build", "dev", "new", "fmt", "test", "doctor"}
TARGETS = ["console", "web", "pwa", "app", "desktop"]


def _normalize_target(target: str, *, announce_alias: bool = False) -> str:
    if target == "app":
        if announce_alias:
            print("Note: '--target app' is now called '--target pwa'. The old name remains as an alias.")
        return "pwa"
    return target


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
    parser.add_argument("--version", action="version", version="Simo 0.6.0")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="Run a console, web, PWA, or desktop project")
    run.add_argument("file", nargs="?", type=Path)
    run.add_argument("--target", choices=TARGETS)
    run.add_argument("--step-limit", type=int, default=100_000)
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8000)
    run.add_argument("--no-open", action="store_true")

    check = subparsers.add_parser("check", help="Parse and validate a project")
    check.add_argument("file", nargs="?", type=Path)

    build = subparsers.add_parser("build", help="Build web, PWA, or native desktop output")
    build.add_argument("file", nargs="?", type=Path)
    build.add_argument("--target", choices=["web", "pwa", "app", "desktop"])
    build.add_argument("--output", "-o", type=Path)
    build.add_argument(
        "--no-install-tools",
        action="store_true",
        help="Do not automatically install the native desktop packager",
    )

    dev = subparsers.add_parser("dev", help="Run a web, PWA, or desktop project in development")
    dev.add_argument("file", nargs="?", type=Path)
    dev.add_argument("--target", choices=["web", "pwa", "app", "desktop"])
    dev.add_argument("--output", type=Path, default=Path(".simo-dev"))
    dev.add_argument("--host", default="127.0.0.1")
    dev.add_argument("--port", type=int, default=8000)
    dev.add_argument("--no-open", action="store_true")

    new = subparsers.add_parser("new", help="Create a Simo project")
    new.add_argument("name", type=Path)
    new.add_argument(
        "--template",
        choices=["console", "web", "pwa", "app", "desktop"],
        default="console",
    )

    fmt = subparsers.add_parser("fmt", help="Format Simo source files")
    fmt.add_argument("files", nargs="+", type=Path)
    fmt.add_argument("--check", action="store_true")

    test = subparsers.add_parser("test", help="Run test_*.simo files")
    test.add_argument("path", nargs="?", type=Path, default=Path("tests"))
    test.add_argument("--step-limit", type=int, default=100_000)

    subparsers.add_parser("doctor", help="Show toolchain and project information")
    return parser


def _project_settings(file: Path | None, explicit_target: str | None):
    project = load_project(file or Path.cwd())
    source = resolve_entry(file)
    target = _normalize_target(explicit_target or project.target, announce_alias=True)
    return project, source, target


def _resolve_build_settings(file: Path | None, target: str | None, output: Path | None):
    project, source, selected_target = _project_settings(file, target)
    if selected_target == "console":
        selected_target = "web"
    selected_output = output.resolve() if output else project.output.resolve()
    return project, source, selected_target, selected_output


def _run_page_target(
    source: Path,
    target: str,
    *,
    output: Path,
    host: str,
    port: int,
    open_browser: bool,
) -> int:
    if target == "desktop":
        return run_desktop(source)
    serve(
        source,
        output,
        target=target,
        host=host,
        port=port,
        open_browser=open_browser,
    )
    return 0


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
            project, source, target = _project_settings(args.file, args.target)
            if target == "console":
                return run_file(source, args.step_limit)
            return _run_page_target(
                source,
                target,
                output=project.root / ".simo-dev",
                host=args.host,
                port=args.port,
                open_browser=not args.no_open,
            )

        if args.command == "check":
            source = resolve_entry(args.file)
            program = load_program(source)
            page_count = sum(
                1 for statement in program.statements if statement.__class__.__name__ == "PageDecl"
            )
            print(f"OK {source} ({len(program.statements)} top-level statements, {page_count} page)")
            return 0

        if args.command == "build":
            project, source, target, output = _resolve_build_settings(
                args.file, args.target, args.output
            )
            if target == "desktop":
                artifact = build_desktop(
                    source,
                    output,
                    project=project,
                    auto_install_tools=not args.no_install_tools,
                )
                print(f"Built native desktop app: {artifact}")
                return 0
            result = build_web_target(source, output, target)
            print(f"Built {target}: {result}")
            if target == "pwa":
                print("The output is an installable Progressive Web App. Serve it over HTTPS to install it.")
            return 0

        if args.command == "dev":
            project, source, target = _project_settings(args.file, args.target)
            if target == "console":
                target = "web"
            output = args.output if args.output.is_absolute() else project.root / args.output
            return _run_page_target(
                source,
                target,
                output=output,
                host=args.host,
                port=args.port,
                open_browser=not args.no_open,
            )

        if args.command == "new":
            template = _normalize_target(args.template, announce_alias=True)
            project = create_project(args.name, template)
            print(f"Created {template} project at {project.root}")
            print(f"Next: cd {project.root.name}")
            if template == "console":
                print("Then: simo run")
            elif template == "desktop":
                print("Then: simo run  # opens a native window")
            else:
                print("Then: simo dev")
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
            print("Simo 0.6.0")
            print(f"Python: {sys.version.split()[0]}")
            print(f"Project root: {project.root}")
            print(f"Entry: {project.entry}")
            print(f"Target: {_normalize_target(project.target)}")
            print(f"Output: {project.output}")
            print(f"Native window runtime: {'ready' if tkinter_available() else 'missing tkinter'}")
            print(
                "Desktop executable packager: "
                + ("ready" if pyinstaller_available() else "will install automatically on first build")
            )
            return 0
    except SimoError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"[IOError] {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

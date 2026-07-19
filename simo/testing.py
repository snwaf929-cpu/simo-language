"""Small test runner for Simo source tests."""

from __future__ import annotations

import io
from pathlib import Path

from simo.interpreter import Interpreter
from simo.source import parse_file


def run_tests(path: Path, step_limit: int = 100_000) -> tuple[int, int]:
    path = path.resolve()
    files = [path] if path.is_file() else sorted(path.rglob("test_*.simo"))
    if not files:
        print(f"No Simo tests found under {path}")
        return 0, 0

    passed = 0
    failed = 0
    for file in files:
        buffer = io.StringIO()
        try:
            program = parse_file(file)
            Interpreter(
                filename=str(file), step_limit=step_limit, output_stream=buffer
            ).interpret(program)
        except Exception as exc:
            failed += 1
            print(f"FAIL {file}: {exc}")
        else:
            passed += 1
            print(f"PASS {file}")
    print(f"\n{passed} passed, {failed} failed")
    return passed, failed

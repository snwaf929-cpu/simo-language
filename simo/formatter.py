"""Conservative source formatter for Simo files."""

from __future__ import annotations

from simo.source import parse_source


def format_source(source: str, filename: str = "<memory>", indent: str = "    ") -> str:
    # Validate first. Formatting invalid input can hide the actual syntax error.
    parse_source(source, filename)

    output: list[str] = []
    level = 0
    for raw in source.splitlines():
        text = raw.strip()
        if not text:
            if output and output[-1] != "":
                output.append("")
            continue

        lower = text.lower()
        closes = (
            lower == "end"
            or lower.startswith("else")
            or lower == "}"
            or lower.startswith("if it fails")
        )
        if closes:
            level = max(0, level - 1)

        output.append(indent * level + text)

        opens = False
        if lower.startswith("action "):
            opens = True
        elif lower.startswith("if ") and not lower.startswith("if it fails"):
            opens = True
        elif lower.startswith("else if ") or lower == "else":
            opens = True
        elif lower.startswith("loop "):
            opens = True
        elif lower == "attempt" or lower.startswith("if it fails"):
            opens = True
        elif text.endswith("{"):
            opens = True
        elif lower.startswith("when ") and text.endswith(":"):
            opens = True

        if opens:
            level += 1

    while output and output[-1] == "":
        output.pop()
    return "\n".join(output) + "\n"

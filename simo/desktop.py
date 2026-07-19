"""Public native desktop runtime API for Simo."""

from __future__ import annotations

from pathlib import Path

from simo.desktop_element import DesktopElement
from simo.desktop_runtime import DesktopRuntime


def run_desktop(source_path: Path) -> int:
    """Open a Simo page in a native desktop window."""

    return DesktopRuntime(source_path).run()


def tkinter_available() -> bool:
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return False
    return True


__all__ = ["DesktopElement", "DesktopRuntime", "run_desktop", "tkinter_available"]

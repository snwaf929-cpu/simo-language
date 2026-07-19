"""Per-user Windows integration for Simo source files."""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
from pathlib import Path

from simo.branding import bundled_icon
from simo.errors import ProjectError


PROG_ID = "Simo.Source"


def _preferred_editor_command() -> str:
    for executable in ("cursor.exe", "cursor", "code.exe", "code"):
        resolved = shutil.which(executable)
        if resolved:
            return f'"{resolved}" "%1"'
    return 'notepad.exe "%1"'


def _persistent_windows_icon() -> Path:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    destination = local_app_data / "Simo" / "icons" / "simo.ico"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundled_icon("ico"), destination)
    return destination


def register_windows_file_type(icon_path: Path | None = None) -> str:
    """Register ``.simo`` as a per-user Windows source-file type.

    This does not require administrator rights. Windows may retain an explicit user
    default-app choice, but the ProgID and Simo icon remain available to Explorer.
    """

    if sys.platform != "win32":
        raise ProjectError("Windows file registration is only available on Windows")

    import winreg

    icon = (icon_path or _persistent_windows_icon()).resolve()
    command = _preferred_editor_command()
    classes = r"Software\Classes"

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{classes}\.simo") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, PROG_ID)
        winreg.SetValueEx(key, "Content Type", 0, winreg.REG_SZ, "text/x-simo")
        winreg.SetValueEx(key, "PerceivedType", 0, winreg.REG_SZ, "text")

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{classes}\{PROG_ID}") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Simo Source File")

    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, rf"{classes}\{PROG_ID}\DefaultIcon"
    ) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{icon}",0')

    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, rf"{classes}\{PROG_ID}\shell\open\command"
    ) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

    try:
        # SHCNE_ASSOCCHANGED tells Explorer to refresh file associations and icons.
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
    except (AttributeError, OSError):
        pass
    return command

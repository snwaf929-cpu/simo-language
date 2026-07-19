"""Simo brand assets and editor integration helpers."""

from __future__ import annotations

import json
import os
import shutil
import struct
from importlib.resources import files
from pathlib import Path


EDITOR_EXTENSION_ID = "simo-language.simo-language-support"


def resource_path(*parts: str) -> Path:
    """Return a filesystem path to a bundled Simo resource."""

    return Path(str(files("simo").joinpath("resources", *parts)))


def _icon_cache() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        root = Path(os.environ["LOCALAPPDATA"]) / "Simo" / "cache"
    elif os.environ.get("XDG_CACHE_HOME"):
        root = Path(os.environ["XDG_CACHE_HOME"]) / "simo"
    else:
        root = Path.home() / ".cache" / "simo"
    path = root / "icons"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _png_dimensions(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Bundled Simo icon is not a valid PNG")
    return struct.unpack(">II", data[16:24])


def _make_ico(png: bytes) -> bytes:
    width, height = _png_dimensions(png)
    width_byte = 0 if width >= 256 else width
    height_byte = 0 if height >= 256 else height
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        width_byte,
        height_byte,
        0,
        0,
        1,
        32,
        len(png),
        6 + 16,
    )
    return header + entry + png


def _make_icns(png: bytes) -> bytes:
    # ic08 is the 256x256 PNG-compressed ICNS element.
    element = b"ic08" + struct.pack(">I", 8 + len(png)) + png
    return b"icns" + struct.pack(">I", 8 + len(element)) + element


def bundled_icon(extension: str) -> Path:
    """Return the official Simo icon as ``png``, ``ico``, or ``icns``.

    The source asset is a transparent PNG. Platform containers are generated with
    the standard library and cached per user, avoiding external image tools.
    """

    normalized = extension.lower().lstrip(".")
    if normalized not in {"ico", "icns", "png"}:
        raise ValueError(f"Unsupported icon format: {extension}")
    source = resource_path("icons", "simo.png")
    if not source.exists():
        raise FileNotFoundError(f"Bundled Simo icon is missing: {source}")
    if normalized == "png":
        return source

    destination = _icon_cache() / f"simo.{normalized}"
    png = source.read_bytes()
    rendered = _make_ico(png) if normalized == "ico" else _make_icns(png)
    if not destination.exists() or destination.read_bytes() != rendered:
        destination.write_bytes(rendered)
    return destination


def editor_extension_source() -> Path:
    path = resource_path("editor")
    if not (path / "package.json").exists():
        raise FileNotFoundError(f"Bundled Simo editor extension is missing: {path}")
    return path


def _extension_version(source: Path) -> str:
    data = json.loads((source / "package.json").read_text(encoding="utf-8"))
    return str(data.get("version", "0.0.0"))


def _editor_locations(editor: str) -> list[tuple[str, Path, str]]:
    home = Path.home()
    available = {
        "vscode": (home / ".vscode" / "extensions", "code"),
        "cursor": (home / ".cursor" / "extensions", "cursor"),
    }
    if editor == "both":
        names = ["vscode", "cursor"]
    elif editor in available:
        names = [editor]
    elif editor == "auto":
        names = [
            name
            for name, (folder, executable) in available.items()
            if folder.parent.exists() or shutil.which(executable)
        ]
    elif editor == "none":
        names = []
    else:
        raise ValueError(f"Unknown editor selection: {editor}")
    return [(name, *available[name]) for name in names]


def install_editor_support(editor: str = "auto") -> list[Path]:
    """Install the bundled Simo extension into VS Code and/or Cursor."""

    source = editor_extension_source()
    version = _extension_version(source)
    installed: list[Path] = []
    for _name, extensions_dir, _executable in _editor_locations(editor):
        extensions_dir.mkdir(parents=True, exist_ok=True)
        destination = extensions_dir / f"{EDITOR_EXTENSION_ID}-{version}"
        for previous in extensions_dir.glob(f"{EDITOR_EXTENSION_ID}-*"):
            if previous != destination and previous.is_dir():
                shutil.rmtree(previous)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        installed.append(destination)
    return installed

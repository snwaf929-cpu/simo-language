"""One-command native executable builder for Simo desktop projects."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from simo import ast_nodes as ast
from simo.branding import bundled_icon
from simo.errors import BuildError
from simo.project import ProjectConfig, load_project
from simo.source import load_program


_PYINSTALLER_REQUIREMENT = "pyinstaller>=6,<7"


def pyinstaller_available() -> bool:
    return importlib.util.find_spec("PyInstaller") is not None


def ensure_pyinstaller(*, auto_install: bool = True) -> None:
    if pyinstaller_available():
        return
    if not auto_install:
        raise BuildError(
            "Desktop bundling needs Simo's native packager. Re-run without "
            "--no-install-tools to let Simo install it automatically."
        )
    print("Installing the Simo desktop packager (one-time setup)...")
    command = [sys.executable, "-m", "pip", "install", _PYINSTALLER_REQUIREMENT]
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BuildError(
            "Simo could not install the desktop packager automatically. "
            f"Run: {sys.executable} -m pip install '{_PYINSTALLER_REQUIREMENT}'"
        ) from exc
    if not pyinstaller_available():
        raise BuildError("The desktop packager was installed but cannot be imported")


def _safe_name(name: str) -> str:
    rendered = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-.")
    return rendered or "simo-app"


def _validate_output(project: ProjectConfig, output_dir: Path) -> None:
    project_root = project.root.resolve()
    if output_dir == project_root or output_dir in project_root.parents:
        raise BuildError(
            "Desktop output cannot be the project directory or one of its parents",
            str(output_dir),
        )


def _stage_project(project: ProjectConfig, source_path: Path, destination: Path) -> Path:
    """Copy Simo source and declared assets, never unrelated project files."""

    root = project.root.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for source in root.rglob("*.simo"):
        if any(part.startswith(".") for part in source.relative_to(root).parts):
            continue
        relative = source.relative_to(root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    config = root / "simo.toml"
    if config.exists():
        shutil.copy2(config, destination / "simo.toml")
    assets = root / "assets"
    if assets.is_dir():
        shutil.copytree(assets, destination / "assets", dirs_exist_ok=True)

    try:
        entry_relative = source_path.relative_to(root)
    except ValueError:
        entry_relative = Path("main.simo")
        shutil.copy2(source_path, destination / entry_relative)
    if not (destination / entry_relative).exists():
        raise BuildError("Desktop entry source was not staged", str(source_path))
    return entry_relative


def _platform_icon(project: ProjectConfig) -> Path:
    """Return a project icon when supplied, otherwise Simo's bundled logo."""

    assets = project.root / "assets"
    if sys.platform == "win32":
        candidate = assets / "icon.ico"
        return candidate if candidate.exists() else bundled_icon("ico")
    if sys.platform == "darwin":
        candidate = assets / "icon.icns"
        return candidate if candidate.exists() else bundled_icon("icns")
    candidate = assets / "icon.png"
    return candidate if candidate.exists() else bundled_icon("png")


def build_desktop(
    source_path: Path,
    output_dir: Path,
    *,
    project: ProjectConfig | None = None,
    auto_install_tools: bool = True,
) -> Path:
    """Bundle a Simo page into a native executable for the current OS."""

    source_path = source_path.resolve()
    output_dir = output_dir.resolve()
    project = project or load_project(source_path)
    _validate_output(project, output_dir)

    program = load_program(source_path)
    pages = [statement for statement in program.statements if isinstance(statement, ast.PageDecl)]
    if len(pages) != 1:
        raise BuildError(
            "Native desktop builds require exactly one page declaration",
            str(source_path),
        )
    ensure_pyinstaller(auto_install=auto_install_tools)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    app_name = _safe_name(project.name)

    with tempfile.TemporaryDirectory(prefix="simo-desktop-") as temporary:
        temporary_root = Path(temporary)
        staged_app = temporary_root / "app"
        entry_relative = _stage_project(project, source_path, staged_app)

        launcher = temporary_root / "simo_desktop_launcher.py"
        launcher.write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "from simo.desktop import run_desktop\n\n"
            "base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))\n"
            f"source = base / 'app' / {str(entry_relative.as_posix())!r}\n"
            "raise SystemExit(run_desktop(source))\n",
            encoding="utf-8",
        )

        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--name",
            app_name,
            "--distpath",
            str(output_dir),
            "--workpath",
            str(temporary_root / "work"),
            "--specpath",
            str(temporary_root / "spec"),
            "--collect-submodules",
            "simo",
            "--collect-data",
            "simo",
            "--hidden-import",
            "tkinter",
            "--hidden-import",
            "tkinter.filedialog",
            "--hidden-import",
            "tkinter.messagebox",
            "--hidden-import",
            "tkinter.simpledialog",
            "--add-data",
            f"{staged_app}{os.pathsep}app",
            "--icon",
            str(_platform_icon(project)),
            str(launcher),
        ]

        try:
            subprocess.run(command, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise BuildError(
                "Native desktop packaging failed. Run 'simo doctor' and review the "
                "packager output above.",
                str(source_path),
            ) from exc

    candidates = [
        output_dir / f"{app_name}.exe",
        output_dir / f"{app_name}.app",
        output_dir / app_name,
    ]
    artifact = next((candidate for candidate in candidates if candidate.exists()), None)
    if artifact is None:
        produced = sorted(output_dir.iterdir())
        artifact = produced[0] if produced else None
    if artifact is None:
        raise BuildError(
            "Desktop packager completed without producing an application",
            str(source_path),
        )
    return artifact

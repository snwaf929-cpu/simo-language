"""Project configuration and templates for Simo."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from simo.errors import ProjectError


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    name: str
    entry: Path
    target: str = "console"
    output: Path = Path("dist")


def load_project(start: Path | None = None) -> ProjectConfig:
    start = (start or Path.cwd()).resolve()
    directory = start if start.is_dir() else start.parent
    config_path: Path | None = None
    for candidate in [directory, *directory.parents]:
        path = candidate / "simo.toml"
        if path.exists():
            config_path = path
            break
    if config_path is None:
        root = directory
        entry = root / "main.simo"
        return ProjectConfig(root, root.name, entry, "console", root / "dist")

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ProjectError(f"Cannot read {config_path}: {exc}", str(config_path)) from exc
    project = data.get("project", {})
    root = config_path.parent
    name = str(project.get("name", root.name))
    entry = root / str(project.get("entry", "main.simo"))
    target = str(project.get("target", "console"))
    if target == "app":
        target = "pwa"
    output = root / str(project.get("output", "dist"))
    return ProjectConfig(root, name, entry, target, output)


def resolve_entry(file: Path | None = None) -> Path:
    if file is not None:
        return file.resolve()
    config = load_project()
    if not config.entry.exists():
        raise ProjectError(
            "No source file was supplied and the project entry does not exist. "
            "Create main.simo or configure [project].entry in simo.toml.",
            str(config.entry),
        )
    return config.entry.resolve()


def create_project(destination: Path, template: str = "console") -> ProjectConfig:
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ProjectError(f"Directory is not empty: {destination}", str(destination))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "assets").mkdir(exist_ok=True)

    if template == "app":
        template = "pwa"
    if template not in {"console", "web", "pwa", "desktop"}:
        raise ProjectError(f"Unknown project template '{template}'", str(destination))

    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", destination.name).strip("-") or "simo-project"
    config = (
        f'[project]\nname = "{safe_name}"\nentry = "main.simo"\n'
        f'target = "{template}"\noutput = "dist"\n'
    )
    (destination / "simo.toml").write_text(config, encoding="utf-8")
    (destination / ".gitignore").write_text(
        "dist/\n.simo-dev/\n__pycache__/\n.simo-storage.json\n",
        encoding="utf-8",
    )

    if template == "console":
        source = '''set name = "World"\n\naction greet(person)\n    say("Hello, " + person + "!")\nend\n\ngreet(name)\n'''
    elif template == "desktop":
        app_title = destination.name.replace("-", " ").replace("_", " ").title()
        source = f'''page "{app_title}" size 460x520 {{
    show heading "{app_title}" named title {{
        size big
        align center
    }}

    show input box named first_number placeholder "First number"
    show input box named second_number placeholder "Second number"
    show text "Result: 0" named result_text

    show button "Add" named add_button {{
        background #17191c
        color white
        when clicked:
            set result = number(first_number.value) + number(second_number.value)
            change text of result_text to "Result: " + result
        end
    }}
}}
'''
    else:
        app_title = destination.name.replace("-", " ").replace("_", " ").title()
        source = f'''page "{app_title}" size 720x520 {{
    set count = 0

    show heading "{app_title}" named title {{
        size big
        align center
    }}

    show text "Count: " + count named counter_text

    show button "Add one" named add_button {{
        rounded
        when clicked:
            count = count + 1
            change text of counter_text to "Count: " + count
        end
    }}
}}
'''
    (destination / "main.simo").write_text(source, encoding="utf-8")

    if template == "console":
        run_command = "simo run"
    elif template == "desktop":
        run_command = "simo run  # opens the native app\nsimo build --target desktop  # creates an executable"
    else:
        run_command = "simo dev\nsimo build"
    (destination / "README.md").write_text(
        f"# {destination.name}\n\nEdit `main.simo`, then run:\n\n```bash\n{run_command}\n```\n",
        encoding="utf-8",
    )
    return load_project(destination)

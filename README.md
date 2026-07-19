# Simo Programming Language

Simo is a readable programming language for console programs, websites, installable Progressive Web Apps, and native desktop applications. Application authors edit `.simo` files; generated browser files and native packaging files are build artifacts, not source code.

> Current release: **0.6.0 alpha**. Native desktop run/build is now available. Mobile packaging, the game target, the package registry, and the full language server remain under development.

## Install

Simo requires Python 3.11 or newer.

```bash
python -m pip install "git+https://github.com/snwaf929-cpu/simo-language.git"
```

On Windows:

```powershell
py -m pip install "git+https://github.com/snwaf929-cpu/simo-language.git"
```

Verify the installation:

```bash
simo --version
simo doctor
```

## Native desktop: `.simo` only

Create a calculator project:

```bash
simo new my-calculator --template desktop
cd my-calculator
simo run
```

`Simo run` reads `simo.toml`, sees the `desktop` target, and opens `main.simo` in a real native window. No Rust, Tauri, Electron project, HTML editing, or manual wrapper is required.

Build an executable for the current operating system:

```bash
simo build --target desktop
```

The first desktop build automatically installs Simo's PyInstaller-based packager when it is not already available. The resulting application includes Python and the Simo runtime, so the person running the finished executable does not need to install Simo or Python.

Desktop builds are host-specific:

- Windows builds a Windows `.exe`.
- macOS builds a macOS application/binary.
- Linux builds a Linux executable.

Build each platform on that platform or in a matching CI runner.

### Desktop example

```simo
page "Calculator" size 460x520 {
    show heading "Calculator" named title {
        size big
        align center
    }

    show input box named first_number placeholder "First number"
    show input box named second_number placeholder "Second number"
    show text "Result: 0" named result_text

    show button "Add" named add_button {
        background #17191c
        color white

        when clicked:
            set result = number(first_number.value) + number(second_number.value)
            change text of result_text to "Result: " + result
        end
    }
}
```

## Other project types

Console:

```bash
simo new hello-simo --template console
cd hello-simo
simo run
```

Website:

```bash
simo new my-site --template web
cd my-site
simo dev
simo build
```

Installable Progressive Web App:

```bash
simo new my-pwa --template pwa
cd my-pwa
simo dev
simo build
```

`--target app` remains as a compatibility alias for `--target pwa`, but new projects and documentation use the accurate `pwa` name.

## Targets

| Target | Main workflow | Output |
|---|---|---|
| Console | `simo run` | Runs through the Simo interpreter |
| Web | `simo dev`, `simo build` | Static HTML, CSS, JavaScript, and assets |
| PWA | `simo dev`, `simo build` | Installable browser app with manifest and service worker |
| Desktop | `simo run`, `simo build` | Native Tk window or packaged native executable |

For web and PWA projects, `dist/index.html`, `styles.css`, and `app.js` are compiler output. Do not edit them. Change `main.simo` and rebuild.

## Native desktop APIs

Desktop page programs can use:

```simo
set selected = open_file_dialog()
set destination = save_file_dialog()
set folder = select_folder()

desktop_notification("Saved", "Your file was saved")
clipboard_set("Copied from Simo")
set copied = clipboard_get()
open_url("https://example.com")
set data_directory = app_data_path()
quit_app()
```

`save(key, value)` and `load(key, fallback)` use a persistent per-user application data directory in desktop builds. `ask(prompt)` opens a native prompt dialog.

## Commands

```text
simo run [file] [--target ...]       Run console/web/PWA/desktop projects
simo check [file]                    Parse and validate source and imports
simo build [file] --target ...       Build web, PWA, or native desktop output
simo dev [file] [--target ...]       Run a development web server or native window
simo new NAME --template ...         Create console/web/PWA/desktop projects
simo fmt FILES...                    Format source files
simo test [path]                     Run test_*.simo files
simo doctor                          Check native and packaging support
```

A `simo.toml` project lets commands omit the file and target:

```toml
[project]
name = "calculator"
entry = "main.simo"
target = "desktop"
output = "dist"
```

## Implemented language features

- Mutable variables and immutable constants
- Numbers, text, booleans, `null`, lists, and objects
- Member access and indexing
- Actions, return values, closures, and imports
- Conditions and fixed/while/collection loops
- `break`, `continue`, and `attempt` / `if it fails`
- Console, file, and persistent-storage helpers
- Page, heading, text, button, image, and input elements
- Click and input-change events
- Element changes and notifications
- Web, PWA, native desktop runtime, and executable packaging
- Formatter, checker, test runner, project generator, and development server
- VS Code syntax definition and snippets under `editors/vscode`

## Documentation

- [Language guide](docs/LANGUAGE.md)
- [Web, PWA, and desktop guide](docs/WEB_AND_APPS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Platform implementation plan](docs/PLATFORM_PLAN.md)
- [Roadmap](docs/ROADMAP.md)

## Development

```bash
git clone https://github.com/snwaf929-cpu/simo-language.git
cd simo-language
python -m pip install -e .
python -m unittest discover -s tests -v
```

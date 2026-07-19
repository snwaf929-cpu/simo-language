# Simo Programming Language

Simo is a readable programming language that can run console programs and compile page programs into websites, installable Progressive Web Apps, and desktop application scaffolds.

> Current release: **0.5.0 alpha**. The core language and web/app toolchain are usable. Native mobile packaging and a dedicated game engine are not part of this release.

## Install

Simo requires Python 3.11 or newer.

```bash
python -m pip install "git+https://github.com/snwaf929-cpu/simo-language.git"
```

On Windows, `py` can be used instead of `python`:

```powershell
py -m pip install "git+https://github.com/snwaf929-cpu/simo-language.git"
```

Verify the installation:

```bash
simo --version
simo doctor
```

## Create a project

Console project:

```bash
simo new hello-simo --template console
cd hello-simo
simo run
```

Website project:

```bash
simo new my-site --template web
cd my-site
simo dev
```

Installable app project:

```bash
simo new my-app --template app
cd my-app
simo dev --target app
simo build --target app
```

## Console example

```simo
set player = { name: "Alex", score: 0 }
set rewards = [10, 20, 30]

action add_points(amount)
    player.score = player.score + amount
end

loop for reward in rewards
    add_points(reward)
end

say(player.name + " scored " + player.score)
```

Run it:

```bash
simo run main.simo
```

## Website example

```simo
page "Counter App" size 600x420 {
    set count = 0

    show heading "Counter" named title {
        size big
        align center
    }

    show text "Count: " + count named counter_text

    show button "Add one" named add_button {
        background #17191c
        color white
        rounded

        when clicked:
            count = count + 1
            change text of counter_text to "Count: " + count
            show notification "Point added"
        end
    }
}
```

Develop locally:

```bash
simo dev main.simo
```

Build static files:

```bash
simo build main.simo --target web
```

The generated `dist/` directory contains `index.html`, `styles.css`, `app.js`, and copied assets. It can be hosted on any static host.

## Build targets

| Target | Command | Output |
|---|---|---|
| Console | `simo run main.simo` | Runs through the Simo interpreter |
| Web | `simo build --target web` | Static HTML, CSS, and JavaScript |
| App | `simo build --target app` | Installable PWA with manifest, icon, and service worker |
| Desktop | `simo build --target desktop` | Web bundle plus a Tauri 2 desktop scaffold |

The desktop target generates the source scaffold. Producing `.exe`, `.msi`, `.dmg`, or Linux bundles requires Rust and the Tauri CLI on the build machine.

## Commands

```text
simo run [file]                 Run a console program
simo check [file]               Parse and validate source and imports
simo build [file] --target ...  Build web, app, or desktop output
simo dev [file]                 Start the development server
simo new NAME --template ...    Create a project
simo fmt FILES...               Format source files
simo test [path]                Run test_*.simo files
simo doctor                     Show environment and project information
```

A `simo.toml` project file lets commands omit the source path:

```toml
[project]
name = "counter-app"
entry = "main.simo"
target = "web"
output = "dist"
```

## Implemented language features

- Mutable `set` variables and immutable `fix` constants
- Numbers, text, booleans, `null`, lists, and objects
- Member access and list/object indexing
- Actions, return values, lexical closures, and imports
- `if`, `else if`, `else`
- Fixed, while, and collection loops
- `break` and `continue`
- `attempt` / `if it fails`
- Console input/output and file/storage helpers
- Page, heading, text, button, image, and input elements
- Click and input-change events
- DOM changes and notifications
- Web, PWA, and desktop-scaffold compilation
- Formatter, project generator, checker, test runner, and development server
- VS Code syntax definition and snippets under `editors/vscode`

## Documentation

- [Language guide](docs/LANGUAGE.md)
- [Web and app guide](docs/WEB_AND_APPS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)

## Development

```bash
git clone https://github.com/snwaf929-cpu/simo-language.git
cd simo-language
python -m pip install -e .
python -m unittest discover -s tests -v
simo build examples/web/main.simo --target web --output dist-example
```

# Architecture

```text
Simo source (.simo only)
  -> Lexer
  -> Tokens
  -> Recursive-descent parser
  -> Shared AST
       -> Console interpreter
       -> Browser compiler
            -> Web
            -> PWA
       -> Native desktop interpreter
            -> Tk widgets and desktop APIs
       -> Desktop packager
            -> PyInstaller
            -> host-native executable
```

## Modules

| Module | Responsibility |
|---|---|
| `lexer.py` | Source characters to tokens |
| `parser.py` and parser mixins | Tokens to AST |
| `ast_nodes.py` | Shared language representation |
| `environment.py` | Lexical bindings and constants |
| `interpreter.py` and interpreter mixins | Console execution and standard library |
| `desktop.py` | Native page runtime, widgets, events, dialogs, clipboard, and storage |
| `desktop_build.py` | Automatic one-file native executable packaging |
| `source.py` | Parsing and import expansion |
| `web.py` and web mixins | HTML/CSS/JavaScript and PWA output |
| `project.py` | `simo.toml` and project templates |
| `devserver.py` | Local browser development server |
| `formatter.py` | Conservative source formatting |
| `testing.py` | Source-level test runner |
| `cli.py` | Target inference and command routing |

All execution targets consume the same AST. Desktop execution does not compile through HTML or require a web shell; it directly maps Simo page nodes to native widgets. Packaged desktop applications embed the runtime and project source as internal application resources.

## Generated output policy

Generated files are implementation details:

- Web/PWA: HTML, CSS, JavaScript, manifest, and service worker
- Desktop: staging files, embedded runtime, and executable

Users author `.simo`, `simo.toml`, and assets. Generated output must never become a required editable layer.

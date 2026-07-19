# Architecture

```text
Simo source
  -> Lexer
  -> Tokens
  -> Recursive-descent parser
  -> Shared AST
       -> Tree-walking console interpreter
       -> JavaScript/DOM web compiler
            -> Static website
            -> PWA application
            -> Tauri desktop scaffold
```

## Modules

| Module | Responsibility |
|---|---|
| `lexer.py` | Source characters to tokens |
| `parser.py` | Tokens to AST |
| `ast_nodes.py` | Shared language representation |
| `environment.py` | Lexical bindings and constants |
| `interpreter.py` | Console execution and standard library |
| `source.py` | Parsing and import expansion |
| `web.py` | HTML/CSS/JavaScript, PWA, and desktop output |
| `project.py` | `simo.toml` and project templates |
| `devserver.py` | Local development server |
| `formatter.py` | Conservative source formatting |
| `testing.py` | Source-level test runner |
| `cli.py` | Command routing |

The compiler and interpreter consume the same AST, keeping syntax consistent across targets.

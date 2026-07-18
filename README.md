# Sola Interpreter (Milestone 1)

Python interpreter for the [Sola programming language](https://github.com/snwaf929-cpu/sola-language) — Milestone 1 covers Sections 2–7 of the specification, limited to the functionality required by the Section 16 example program.

## Installation

Requires **Python 3.11+**.

```bash
cd Sola-ProgrammingLanguage
pip install -e .
```

## Run

```bash
python -m sola examples/section16.sola
```

Or, after installation:

```bash
sola run examples/section16.sola
```

Optional execution step limit (default: 100000):

```bash
python -m sola examples/section16.sola --step-limit 50000
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Supported syntax (Milestone 1)

| Feature | Syntax |
|---|---|
| Mutable variables | `set name = value` |
| Constants | `fix name = value` |
| Assignment | `name = value` |
| Numbers | `0`, `3.14` |
| Strings | `"hello"` |
| Booleans | `true`, `false`, `yes`, `no` |
| Functions | `action name(a, b) ... end` |
| Return | `return expr` |
| Output | `say(expr)` |
| Conditionals | `if ... else if ... else ... end` |
| Fixed loops | `loop N times ... end` |
| Conditional loops | `loop while condition ... end` |
| Comments | `// comment` |
| Operators | `+ - * / == != < <= > >= and or not` |
| Aliases | `is` (`==`), `is not` (`!=`) |

## Not implemented (future milestones)

- Lists and objects (Section 3 lists/objects, Section 8)
- `loop for item in list`
- Error handling (`attempt` / `if it fails`)
- Concurrency (`start`, `wait`)
- UI and app generation (`page`, `show`)
- Games (`scene`, `sprite`, `every frame`)
- Input (keyboard, mouse, touch, `control`)
- Time (`time()`, `frame`, `delta_time`)
- Build targets (`sola build --target web/app`)
- Transpilation
- `note:` comments

## Architecture

```
Source → Lexer → Tokens → Parser → AST → Interpreter → Output
                              ↓
                        Environment (lexical scopes)
```

| Module | Responsibility |
|---|---|
| `sola/tokens.py` | Token type definitions |
| `sola/lexer.py` | Tokenization and `//` comments |
| `sola/ast_nodes.py` | AST node dataclasses |
| `sola/parser.py` | Recursive-descent parser |
| `sola/environment.py` | Lexical environments and bindings |
| `sola/interpreter.py` | Tree-walking evaluator |
| `sola/errors.py` | Lex, parse, and runtime errors |
| `sola/cli.py` | Command-line entry point |

## Known assumptions

1. **Numbers** — integers and decimal floats are supported; division always produces a float.
2. **Strings** — double-quoted with escapes `\\`, `\"`, `\n`, `\t`.
3. **Blocks** — indentation is cosmetic; blocks end at `end`.
4. **`is not`** — recognized as a single comparison operator (two words).
5. **Bare assignment** — `name = value` only updates an existing binding; use `set` to introduce a new variable.
6. **`set` reassignment** — updates the nearest enclosing binding, or creates a local binding if none exists.
7. **`fix` reassignment** — produces a runtime error naming the variable and source line.
8. **Undefined variables** — runtime error on read or bare assignment.
9. **Boolean arithmetic** — booleans are not treated as numbers in arithmetic.
10. **String concatenation** — if either operand of `+` is a string, both sides are converted to readable text (`true`/`false` for booleans).
11. **Equality comparisons** — `==`, `!=`, `is`, and `is not` work with strings, numbers, and booleans; ordering operators (`<`, `<=`, `>`, `>=`) require numbers.
12. **Step limit** — configurable via `--step-limit` to catch accidental infinite loops.
13. **`note:` comments** — not implemented in this milestone.

## License

See the upstream Sola language specification repository for language documentation.

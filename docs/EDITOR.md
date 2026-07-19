# Simo editor intelligence

Install or refresh the bundled VS Code/Cursor extension:

```bash
simo setup-icons --editor both
```

Restart the editor after installation.

## Features

- Syntax colors for declarations, variables, constants, actions, built-ins, object properties, member access, UI names, strings, numbers, colors, and control flow
- Keyword, UI, action, and built-in autocomplete
- Variables, action parameters, named UI elements, and actions discovered from the current file
- Nested object member autocomplete after `.`
- Named UI element properties such as `input.value` and `label.text`
- Signature help while entering action and built-in arguments
- Hover documentation
- Go to definition for variables, actions, and named UI elements
- Page/UI outline symbols
- Fast diagnostics for duplicate declarations, unmatched `end`, and missing braces

## Nested object completion

```simo
set player = {
    back: {
        images: {
            png1: "player.png",
            png2: "enemy.png"
        }
    }
}

set selected = player.back.images.png1
```

After typing:

```simo
player.back.images.
```

the editor suggests `png1` and `png2`.

## UI completion

```simo
show input box named username placeholder "Name"
show text "Welcome" named welcome_text

set entered_name = username.value
change text of welcome_text to entered_name
```

Typing `username.` suggests input properties such as `value`, `placeholder`, `visible`, `enabled`, `color`, and `background`.

## Scope

This release uses a lightweight editor analyzer and does not yet replace the planned full Simo Language Server. It intentionally favors useful, fast suggestions while the compiler-wide semantic analyzer and cross-file LSP are developed.

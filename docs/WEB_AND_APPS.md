# Web, PWA, and Desktop Development

A page program uses the same `.simo` source for browser and native desktop targets:

```simo
page "My App" size 800x600 {
    // state, actions, and native/browser UI elements
}
```

The `.simo` file is the source of truth. Browser files, manifests, service workers, packaging scripts, and executables are generated output.

## Elements

```simo
show heading "Welcome" named heading
show text "Status: Ready" named status
show image "assets/logo.png" named logo {
    alt "Simo logo"
    size 200x100
}
show input box named username placeholder "Enter your name"
show button "Continue" named continue_button
```

Names are required when another expression or statement references an element.

## Styling

```simo
show button "Save" named save_button {
    color white
    background #17191c
    padding 14
    rounded
    width 180
}
```

Web/PWA targets support CSS-oriented attributes. The native desktop runtime maps common attributes such as `size`, `color`, `background`, `width`, `height`, `align`, `visible`, and `enabled` to native widgets. Browser-specific visual details such as arbitrary CSS and pill-shaped borders can differ on desktop.

## Events and element state

```simo
show input box named username placeholder "Name"
show text "Hello" named greeting

show button "Greet" named greet_button {
    when clicked:
        change text of greeting to "Hello, " + username.value
    end
}
```

Input events use `when changes:`. Reactive text can watch an input:

```simo
show text "Hello, " + username.value named live_greeting when username changes
```

## Web

```bash
simo new my-site --template web
cd my-site
simo dev
simo build
```

The generated `dist/` folder can be deployed to a static host. Do not edit `dist`; edit `.simo` source and rebuild.

## Progressive Web App

```bash
simo new my-pwa --template pwa
cd my-pwa
simo dev
simo build
```

The PWA target adds a web manifest, icon, offline service worker, and standalone display mode. It is still browser technology, so Simo calls it `pwa` rather than the ambiguous `app` name. `--target app` is retained only as a compatibility alias.

## Native desktop run

```bash
simo new my-calculator --template desktop
cd my-calculator
simo run
```

The page opens in a native Tk window. No generated HTML or Tauri project is used for desktop execution.

Development can also be explicit:

```bash
simo dev --target desktop
simo run --target desktop
```

## Native executable build

```bash
simo build --target desktop
```

Simo validates the project, stages only project source/assets, automatically installs its packager when needed, and creates a single-file native application for the current operating system. The generated executable embeds the Simo and Python runtimes.

Use `--no-install-tools` in controlled CI environments where automatic installation is not allowed:

```bash
simo build --target desktop --no-install-tools
```

In that mode, install `pyinstaller>=6,<7` ahead of time.

## Desktop APIs

```simo
set source = open_file_dialog()
set destination = save_file_dialog()
set directory = select_folder()

desktop_notification("Export complete", destination)
clipboard_set(destination)
open_url("https://example.com")

save("last-file", destination)
set previous = load("last-file", "")
set data_dir = app_data_path()
```

Available desktop-only helpers:

| Helper | Purpose |
|---|---|
| `open_file_dialog()` | Native open-file dialog |
| `save_file_dialog()` | Native save-file dialog |
| `select_folder()` | Native directory picker |
| `desktop_notification(title, message)` | Native message dialog |
| `clipboard_get()` / `clipboard_set(value)` | System clipboard |
| `open_url(url)` | Open the default browser |
| `app_data_path()` | Per-user persistent application data directory |
| `quit_app()` | Close the application |

`ask(prompt)` also becomes a native dialog inside a desktop page.

## Images

Put assets next to the project under `assets/`:

```simo
show image "assets/logo.png" named logo
```

The browser target supports browser image formats. The native Tk runtime currently supports PNG and GIF directly. More image codecs are planned.

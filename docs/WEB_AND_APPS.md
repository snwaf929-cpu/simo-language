# Web and App Development

## Page declaration

A browser project requires exactly one page:

```simo
page "My App" size 800x600 {
    // state, actions, and UI elements
}
```

The size controls the preferred application surface. The generated page remains responsive on smaller screens.

## Elements

```simo
show heading "Welcome" named heading
show text "Status: Ready" named status
show image "assets/logo.png" named logo {
    alt "Simo logo"
    size 200x100
    rounded
}
show input box named username placeholder "Enter your name"
show button "Continue" named continue_button
```

Names become stable element IDs and are required when another statement references an element.

## Styling attributes

Attributes can be inline or in an element block:

```simo
show button "Save" named save_button {
    color white
    background #17191c
    padding 14
    rounded
    width 180
}
```

Common attributes include `size`, `color`, `background`, `width`, `height`, `padding`, `margin`, `align`, `position`, `rounded`, `visible`, and `alt`.

## Events

```simo
show button "Add" named add_button {
    when clicked:
        count = count + 1
        change text of counter to "Count: " + count
    end
}
```

Input events use `when changes:` inside an input block. Reactive text can also watch an input directly:

```simo
show input box named username placeholder "Name"
show text "Hello, " + username.value named greeting when username changes
```

## UI commands

```simo
change text of status to "Saved"
change color of status to "green"
change visible of panel to false
show notification "Saved successfully"
```

## Assets

Put static files in an `assets/` directory next to the entry file. Builds copy that directory to the output unchanged.

```simo
show image "assets/photo.jpg" named photo
```

## Web build

```bash
simo build main.simo --target web --output dist
```

Deploy the output to any static host.

## Installable app build

```bash
simo build main.simo --target app --output dist
```

This adds a web manifest, service worker, and icon. Host the output over HTTPS; supported browsers can install it as an app.

## Desktop build

```bash
simo build main.simo --target desktop --output dist
```

This adds a Tauri 2 project under `dist/src-tauri`. Install Rust and the Tauri CLI, enter the output directory, and run:

```bash
cargo tauri build
```

The resulting native package depends on the operating system used for the build.

## Development server

```bash
simo dev main.simo --port 8000
```

The browser opens automatically. Source and asset changes are rebuilt on the next browser request. Refresh the page to load the new output.

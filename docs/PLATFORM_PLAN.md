# Platform Implementation Plan

This plan keeps one rule across every platform: developers author `.simo` source and assets only.

## Shared compiler front end

Every target uses:

```text
source -> lexer -> parser -> shared AST -> semantic validation -> target backend
```

The next compiler-wide layer should be a semantic analyzer that resolves bindings, validates target capabilities, and emits target-neutral source locations. That layer is required for reliable LSP diagnostics and source maps.

## Desktop next steps

The shipped Tk runtime is the default zero-setup desktop backend. Planned additions:

- Native menus and keyboard shortcuts
- Multiple windows and dialogs declared in Simo
- Drag/drop and system tray APIs
- Background tasks with safe UI dispatch
- Application permissions and capability declarations in `simo.toml`
- Optional richer desktop renderer while preserving the same page AST
- CI commands for Windows/macOS/Linux release builds and signing

## Mobile backend

Mobile should not reuse generated desktop wrappers. The proposed pipeline is:

```text
Simo page AST -> mobile UI IR -> Android/iOS renderer -> signed package
```

Initial mobile scope:

- Shared layout, text, images, buttons, inputs, navigation, storage, networking, and notifications
- `simo build --target android` and `--target ios`
- Device/simulator launch through `simo run --target android|ios`
- Capability declarations for camera, files, notifications, and network access

Packaging toolchains can be downloaded and managed by Simo, but platform signing credentials remain user-owned.

## Game backend

Game syntax should compile to a dedicated runtime rather than ordinary page widgets:

```simo
scene "Level 1" size 1280x720 {
    sprite player {
        image "assets/player.png"
        x 100
        y 300
        speed 240
    }

    every frame
        if control "move_right" is down
            player.x = player.x + player.speed * delta_time
        end
    end
}
```

Proposed stages:

1. Canvas 2D browser runtime with fixed/update loops.
2. Unified keyboard, mouse, gamepad, and touch controls.
3. Audio, animation, collision, camera, and scene switching.
4. Desktop packaging through the existing executable pipeline.
5. Optional WebGL renderer and physics module.

## Tooling

### LSP

The language server will reuse the parser and semantic analyzer for:

- Diagnostics
- Completion
- Hover documentation
- Definition/references
- Rename
- Formatting
- Target-specific capability warnings

### Source maps

Every AST node already carries line/column data. Backends should emit generated-code mappings to the original `.simo` location. Browser exceptions and desktop runtime errors can then report Simo source lines.

### Components and routing

Components should be ordinary typed UI-producing declarations in the shared UI IR. Routing belongs above web/mobile/desktop renderers so the same navigation model works across targets.

### Package registry

Packages require:

- `simo.toml` dependency declarations
- Lock file with hashes
- Namespaces and semantic versioning
- Cached downloads
- Target capability metadata
- Registry signing and malware review policies

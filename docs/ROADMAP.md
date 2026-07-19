# Roadmap

Simo 0.6 provides console execution, browser/PWA compilation, native desktop execution, automatic desktop executable packaging, and initial desktop system APIs.

## Completed platform foundation

- Native `simo run` and `simo dev` for desktop projects
- `simo new --template desktop`
- One-command host-native executable generation
- Automatic desktop packager installation
- Native file/folder dialogs, prompts, notifications, clipboard, URL opening, and persistent app data
- Accurate `pwa` target name; `app` retained only as a deprecated compatibility alias
- `.simo` remains the only authored application source

## Toward 1.0

1. Language Server Protocol implementation with live diagnostics, completion, rename, and go-to-definition.
2. Published and signed VS Code extension package.
3. Source maps and browser/native stack traces mapped back to `.simo` lines.
4. Components, page routing, reusable UI modules, and application state patterns.
5. Richer native desktop controls, menus, tray icons, drag/drop, background tasks, and OS permission handling.
6. Automated signed release artifacts and cross-platform CI builders.
7. Package registry, semantic versions, dependency lock file, and reproducible builds.
8. Mobile backend and packaging for Android/iOS from the shared page AST.
9. Canvas/WebGL game target with `scene`, `sprite`, `every frame`, controls, audio, collision, and optional physics.
10. Performance optimization, compatibility policy, security review, and formal 1.0 specification.

See [PLATFORM_PLAN.md](PLATFORM_PLAN.md) for the proposed mobile, game, and tooling architecture.

Backward compatibility is not guaranteed before 1.0.

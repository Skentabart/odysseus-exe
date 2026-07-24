# Windows Native Build Plan

This repository now contains the first implementation primitives for the Windows-native port: path resolution, JSON configuration, local file storage, backend launch supervision, diagnostics redaction, and hardware recommendation helpers. These are intentionally small and dependency-light so they can be wired into the upstream backend without requiring Docker, Node.js, PostgreSQL, Redis, MinIO, or OpenSearch on end-user machines.

## Target build command

```powershell
.\build_windows.ps1
```

The final Windows builder must produce:

```text
dist/
├── Odysseus-Setup.exe
└── Odysseus-Portable.zip
```

## Planned build stages

1. Clean `dist/` and temporary build directories.
2. Run Python tests, including `tests/windows/`.
3. Build or copy static frontend assets.
4. Bundle the backend with an embedded Python runtime or frozen executable.
5. Bundle `Odysseus.exe` desktop shell and WebView2/Tauri resources.
6. Copy optional runtimes into `bin/`, including `llama-server.exe` when selected.
7. Assemble installed-app layout.
8. Assemble portable layout with adjacent `data/` mode.
9. Build installer with Inno Setup or WiX.
10. Run smoke tests against the assembled backend and launcher.

## Current state

The complete installer is not implemented yet. The current committed implementation establishes reusable primitives that later stages can import instead of reintroducing Docker-only paths or direct filesystem writes.

## Newly implemented primitives

- SQLite FTS5 search is available as an embedded local-search MVP. It does not replace semantic vector retrieval yet, but it removes the need for an OpenSearch-style server for baseline document lookup.
- Diagnostics export now creates a ZIP containing redacted config and logs while excluding documents, uploads, models, memory, and cache payloads.
- The llama.cpp runtime manager builds a loopback-only `llama-server.exe` command and validates runtime/model paths before start.
- The MCP process manager starts configured local MCP commands as child processes and can stop all managed processes during application shutdown.

## Installer scaffold

`packaging/inno/Odysseus.iss` defines the first Inno Setup installer script. The PowerShell build attempts to compile it when `iscc.exe` is available and otherwise emits a warning instead of pretending that `Odysseus-Setup.exe` exists. User data under `%LOCALAPPDATA%\Odysseus` is intentionally outside the installer payload and is preserved on uninstall.

## Model manager scaffold

`windows_native.models.ModelRegistry` lists, validates, and deletes managed `.gguf` files under the model directory. Deletion is restricted to files inside the managed models directory to avoid accidentally removing a user-selected external model path.

## Runtime orchestrator scaffold

`windows_native.orchestrator.WindowsNativeRuntime` now wires together local storage, SQLite FTS search, SQLite migrations, model registry, MCP process management, logging, backend launch, and optional llama.cpp runtime launch. This is the integration point intended for the future desktop shell.

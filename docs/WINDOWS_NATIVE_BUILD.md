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

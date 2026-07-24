# Odysseus Windows Native Architecture Audit

Status: audit and migration plan only. This document intentionally avoids claiming that a native Windows build is complete. The local checkout used for this change was an empty bootstrap repository, so the source audit below is based on the upstream `odysseus-dev/odysseus` `dev` and `main` repository views and raw files that were accessible during the audit.

## Branch baseline decision

Odysseus currently documents two long-lived branches: `dev` receives all pull requests first and can be in flux, while `main` is the curated branch intended for users. Both `dev` and `main` expose the same top-level application structure relevant to this audit (`app.py`, `routes/`, `src/`, `static/`, `services/`, `mcp_servers/`, `docker-compose.yml`, `Dockerfile`, Windows helper scripts, and tests). For a stable Windows-native base, use `main` for release packaging and cherry-pick narrowly scoped Windows-native work from `dev` only after tests pass. For contribution workflow, open PRs against `dev`.

## Current repository structure

Observed top-level areas:

- `.github/`: CI and repository automation.
- `companion/`: companion integration code.
- `config/searxng/`: bundled SearXNG configuration template.
- `core/`: shared core logic.
- `docker/`: Docker Compose overlays such as host-Docker and GPU passthrough.
- `docs/`: user and developer documentation.
- `integrations/`: third-party integrations.
- `mcp_servers/`: local MCP server implementations or launch definitions.
- `routes/`: FastAPI route modules.
- `scripts/`: operational scripts, mail polling, maintenance helpers, and CLI tasks.
- `services/`: service-layer modules.
- `src/`: backend business logic: agents, model discovery/serving, memory, documents, email/calendar, tools, research, storage, and auth support.
- `static/`: browser frontend assets.
- `tests/`: pytest coverage.
- `app.py`: FastAPI application entrypoint.
- `Dockerfile`, `docker-compose.yml`, GPU overlays, and Windows/macOS launch/build helpers.

## Current runtime architecture

The current default runtime is a self-hosted web application served by FastAPI/Uvicorn on port `7000`, with static frontend assets served from the same process. Docker Compose starts the Odysseus app container plus supporting local services. The default database is already SQLite (`sqlite:///./data/app.db`), which is favorable for Windows-native packaging. The app also supports external OpenAI-compatible LLM endpoints, Ollama, LM Studio, local embeddings through fastembed, ChromaDB for vector storage, SearXNG for metasearch, ntfy for notifications, Google OAuth/Gmail, IMAP/SMTP, CalDAV, MCP, 2FA, scheduled tasks, uploads, documents, and shell/script tools.

## Docker Compose service audit

| Service | Current Technology | Purpose | Dependent Features | Windows Native Replacement | Process Model |
| --- | --- | --- | --- | --- | --- |
| `odysseus` | Python 3.11+ FastAPI/Uvicorn container | Main backend, frontend, auth, routes, agents, tools, documents, email/calendar, memory, model management | All UI and API features | Package backend with embedded Python runtime or PyInstaller/Nuitka; bind to `127.0.0.1`; supervise from `Odysseus.exe` | Child process launched by desktop shell |
| `chromadb` | `chromadb/chroma` server | Vector store for RAG, semantic memory, and tool selection | Document retrieval, memory search, semantic tool ranking | Phase 1: embedded SQLite FTS5 + local embeddings fallback; Phase 2: optional embedded vector index such as sqlite-vec/LanceDB; keep `VectorStore` abstraction | Embedded library, not a server |
| `searxng` | `searxng/searxng` container | Local metasearch for web research | Deep Research, web search tools | Default to external search APIs or direct HTTP provider adapters; optional bundled local SearXNG is not MVP because it is a Python web service with its own dependency/config lifecycle | Disabled by default; optional separate process later |
| `ntfy` | `binwiederhier/ntfy` server | Local push notification broker | Reminders, task/mail notifications if enabled | Windows toast notifications via Tauri plugin or WinRT; keep ntfy remote URL support as optional | Embedded desktop API, no local server |

## Dependency audit

### Python dependencies

Core dependencies include FastAPI, Uvicorn, multipart upload handling, dotenv/settings, HTTP clients, Pydantic, SQLAlchemy, PDF parsing, BeautifulSoup, charset detection, NumPy, ChromaDB HTTP client, fastembed, YouTube transcript extraction, Markdown rendering, HTML sanitization, iCalendar, dateutil recurrence, CalDAV, cryptography, bcrypt, MCP, pyotp, QR code generation, croniter, pytest, and pytest-asyncio.

Windows impact:

- FastAPI/Uvicorn can run natively when packaged with Python.
- SQLAlchemy with SQLite is compatible and should remain the default.
- fastembed downloads ONNX models and needs cache relocation to `%LOCALAPPDATA%\Odysseus\cache\fastembed`.
- ChromaDB client currently assumes a server; replace through a vector-store abstraction.
- CalDAV, IMAP/SMTP, OAuth, and HTTP providers remain external-network features.
- `mcp` can work if local MCP servers are launched as child processes without Docker.
- Native packaging must pin wheels known to install on Windows and avoid build-from-source at user install time.

### Node dependencies

The observed `package.json` only lists `@antithesishq/bombadil` as a dev dependency. The frontend appears to be mostly static HTML/CSS/JavaScript under `static/`, so a Tauri/WebView2 shell can load bundled static assets without requiring Node.js for end users. Node may still be used by contributors or CI for checks, but it must not be part of the installed app prerequisite list.

### Database and migrations

The default `DATABASE_URL` is already SQLite. This makes PostgreSQL unnecessary for the MVP unless hidden optional deployment modes use PostgreSQL. The Windows app should set the database to `%LOCALAPPDATA%\Odysseus\database\app.db` in installed mode and `Odysseus-Portable\data\database\app.db` in portable mode. Migration requirements:

1. Preserve existing SQLAlchemy model metadata and migration logic.
2. Add a startup migration runner that works on SQLite.
3. Provide an export/import command for existing Docker users: copy `./data/app.db` into the Windows data directory when the source is SQLite.
4. If a user has an external PostgreSQL database, document a later `pg_dump` to SQLite migration path and do not auto-migrate until schema compatibility is verified.

## Feature subsystem audit

| Subsystem | Current behavior | Native Windows adaptation |
| --- | --- | --- |
| Authentication | Auth enabled by default; first admin user/password bootstrap; 2FA with pyotp/qrcode | Keep backend auth. Store app secrets under config and API keys in Windows Credential Manager where possible. Localhost bypass must remain off by default. |
| Agents/tools/skills | Agents use LLM providers, tools, files, memory, shell, and MCP | Preserve APIs. Add Windows capability gates for shell and subprocess tools. Document security prompts for local command execution. |
| MCP | Python `mcp` package and `mcp_servers/` | Add `McpProcessManager` for local child processes with Windows-safe command lines, env, cwd, logging, and shutdown. Remote MCP remains URL/config based. |
| Memory/RAG | ChromaDB service plus fastembed fallback | Replace server dependency with `VectorStore` abstraction; implement SQLite FTS5 keyword baseline first, then embedded vector backend. |
| Documents/files/uploads | Stored under Docker-mounted `/app/data` | Introduce `StorageBackend` with `LocalStorage` default rooted at `%LOCALAPPDATA%\Odysseus\data` and optional `S3Storage` later. |
| Web research | SearXNG default plus external search keys | Make SearXNG optional. Provide Brave/Google/Tavily/Serper provider selection; if no provider is configured, show degraded mode. |
| Email | IMAP/SMTP and Google OAuth | Keep as backend integrations. OAuth redirect must target `http://127.0.0.1:<port>/api/email/oauth/google/callback`; secrets must not be stored in Git/config plaintext if Credential Manager is available. |
| Calendar/tasks | iCalendar import/export, CalDAV sync, croniter scheduled tasks, in-process task runner | Use in-process scheduler for MVP. Ensure Windows sleep/resume and timezone behavior are tested. |
| Notifications | ntfy container | Replace with Windows toast notifications; keep remote ntfy URL optional. |
| Shell tools/scripts | Host/container shell execution and optional SSH | Add Windows shell abstraction. Default to PowerShell with explicit user consent and audit logging. Avoid Linux-only paths and signals. |
| Local model workflows | Cookbook supports model recommendations/downloads/serving; Docker GPU overlays pass GPU devices | Add llama.cpp runtime manager for `llama-server.exe`, GGUF model registry, and OpenAI-compatible local endpoint. |
| External AI providers | OpenAI-compatible endpoints, Ollama, LM Studio, embedding endpoint | Keep provider adapters. In Windows mode, probe `127.0.0.1` for Ollama/LM Studio without `host.docker.internal`. |
| Gallery/image tools | Upload/transform limits exist | Keep local file storage; review any platform-specific image dependencies during packaging. |

## Target Windows-native architecture

```text
Odysseus.exe
  ├─ Tauri/WebView2 desktop shell
  ├─ BackendLauncher
  │   └─ bundled backend process: 127.0.0.1:<dynamic or configured port>
  ├─ AiRuntimeManager
  │   └─ optional llama-server.exe: 127.0.0.1:<private port>
  ├─ LocalStorage
  │   └─ %LOCALAPPDATA%\Odysseus\data or portable data\
  ├─ SQLite
  │   └─ %LOCALAPPDATA%\Odysseus\database\app.db
  ├─ LocalSearch
  │   └─ SQLite FTS5 / embedded vector index
  └─ McpProcessManager
      └─ optional local MCP child processes
```

Installed data layout:

```text
%LOCALAPPDATA%\Odysseus\
├── config\
├── data\
├── database\
├── documents\
├── uploads\
├── memory\
├── models\
├── logs\
└── cache\
```

Portable layout:

```text
Odysseus-Portable\
├── Odysseus.exe
├── runtime\
├── backend\
├── frontend\
├── bin\
└── data\
```

## Components to remove, embed, or keep as processes

### Remove from default end-user product

- Docker Desktop / Docker Engine / WSL / Hyper-V requirements.
- ChromaDB server container as a mandatory dependency.
- SearXNG server container as a mandatory dependency.
- ntfy local server container.
- Host Docker socket integrations from the default desktop build.

### Embed in packaged application

- Python backend runtime.
- Static frontend assets.
- SQLite database access and migrations.
- Local file storage.
- Local search index.
- Hardware detection.
- Diagnostics ZIP export with secret redaction.
- Windows toast notifications.

### Run as separate child processes

- Backend server process supervised by `BackendLauncher`.
- `llama-server.exe` only when a local GGUF model is active.
- Local MCP servers configured by the user.
- Optional helper tools that cannot be safely embedded.

## Windows incompatibility risks

- Linux-style paths (`/app/data`, `/app/logs`, `/app/.ssh`, `/etc/searxng`) must be replaced by `pathlib.Path` and platform path providers.
- POSIX signals/process groups must be abstracted for Windows job objects or process tree termination.
- Shell tools must not assume `/bin/sh`, `bash`, `chmod`, `chown`, `id`, `su-exec`, or Unix permissions.
- Long paths and paths containing spaces/non-ASCII characters need tests.
- Browser OAuth redirects and local API ports may trigger firewall prompts if not bound strictly to loopback.
- Windows Defender can quarantine downloaded model/runtime binaries; downloads need provenance and hashes.
- GPU detection is vendor-specific; CUDA/ROCm assumptions from Docker overlays do not transfer directly to Windows.
- WebView2 availability must be checked by installer or bundled bootstrapper.
- Credential storage differs from dotenv files; API key migration must be explicit and redacted from diagnostics.

## Migration plan

| Current Component | Current Technology | Windows Native Replacement | Migration Difficulty | Priority |
| ----------------- | ------------------ | -------------------------- | -------------------- | -------- |
| Web app container | Dockerized FastAPI/Uvicorn | Bundled backend launched on `127.0.0.1` by Tauri | Medium | P0 |
| Static frontend | Served by backend from `static/` | Bundled WebView2/Tauri assets or backend-served local UI | Low | P0 |
| Database | SQLite by default through SQLAlchemy | SQLite under `%LOCALAPPDATA%\Odysseus\database` | Low | P0 |
| ChromaDB | External container service | `VectorStore` abstraction with SQLite FTS5 MVP, embedded vector backend later | High | P1 |
| fastembed cache | Container/HF cache paths | `%LOCALAPPDATA%\Odysseus\cache\fastembed` | Low | P1 |
| SearXNG | External container service | Optional external search APIs; optional local adapter later | Medium | P2 |
| ntfy | External container service | Windows toast notifications; optional remote ntfy | Medium | P2 |
| MinIO/S3-like storage | Not observed as default Compose service; file data mounted into container | `StorageBackend`: `LocalStorage` now, `S3Storage` optional later | Medium | P0 |
| Ollama/LM Studio access | `host.docker.internal` from container | Probe localhost directly from Windows backend | Low | P1 |
| Local GGUF runtime | Cookbook-managed tools inside container/user cache | `AiRuntimeManager` supervising `llama-server.exe` | High | P1 |
| GPU enablement | Docker Compose NVIDIA/AMD overlays | Native hardware detection + llama.cpp CUDA/Vulkan/CPU binary choice | High | P1 |
| MCP local servers | Python package / repo server scripts | Windows child-process manager with per-server config | Medium | P1 |
| Shell/script tools | Container or host shell/SSH | Windows shell abstraction, PowerShell default, consent/audit logs | High | P2 |
| Scheduled tasks | In-process pollers, croniter | In-process scheduler with Windows sleep/resume handling | Medium | P1 |
| Email/calendar | IMAP/SMTP, Google OAuth, CalDAV | Keep; adapt OAuth redirect, credential storage, path handling | Medium | P2 |
| Auth/2FA | bcrypt, cryptography, pyotp, qrcode | Keep; move secrets to Windows-safe config/credential store | Medium | P0 |
| Installer | Docker/manual scripts | Inno Setup or WiX wrapping Tauri bundle and runtime assets | High | P3 |
| Portable build | Existing helper script | Portable ZIP with adjacent `data` mode | Medium | P3 |
| Updates | Container rebuild/git pull patterns | App update channel separated from user data | High | P4 |

## Iterative implementation order

1. Add platform path/config layer that resolves installed vs portable data roots.
2. Add backend launcher health/status contract and ensure loopback-only binding.
3. Add `StorageBackend` and migrate uploads/documents to `LocalStorage` paths.
4. Add `VectorStore` abstraction and SQLite FTS5 fallback; keep ChromaDB as optional remote backend until fully replaced.
5. Add Windows hardware detection service and model recommendation API.
6. Add llama.cpp runtime manager with GGUF model registry and OpenAI-compatible endpoint wiring.
7. Add Tauri desktop shell with system tray, first-run wizard, diagnostics, and logs.
8. Add Windows-specific tests under `tests/windows/`.
9. Add `build_windows.ps1`, installer definition, portable ZIP assembly, and GitHub Actions release workflow.
10. Only after MVP smoke tests pass, expand web research, email/calendar polish, auto-update, and optional advanced vector search.

## Explicit limitations after this audit

- A complete `Odysseus-Setup.exe` is not implemented by this document.
- ChromaDB replacement requires code changes and test fixtures; the safe MVP path is a feature-gated `VectorStore` abstraction before removing the existing client.
- SearXNG cannot be silently replaced with equivalent private metasearch without either bundling another service or requiring external provider API keys; the native MVP should clearly show web-research degraded mode when no provider is configured.
- Native GPU acceleration depends on distributing or downloading the correct llama.cpp backend binaries; model files must remain user-managed under the data directory.
- Existing Docker users need an explicit data migration utility and documentation before Windows-native releases are advertised as production-ready.

## Implementation progress after audit

The first implementation slice now adds dependency-light Windows-native primitives that can be wired into the upstream application incrementally:

- `windows_native.paths` resolves installed and portable data roots and creates the required `%LOCALAPPDATA%\Odysseus` or adjacent portable `data` directory tree.
- `windows_native.config` reads and writes non-secret JSON configuration and provides diagnostics redaction helpers.
- `windows_native.storage` defines the `StorageBackend` contract and implements safe local file storage with path traversal protection.
- `windows_native.backend_launcher` defines a loopback backend launcher and `/health` polling contract for the future desktop shell.
- `windows_native.hardware` provides the first cross-platform hardware-info and model-recommendation stub; Windows-specific GPU/VRAM probing is still TODO.
- `tests/windows/` covers path resolution, portable mode, Unicode paths, config round-tripping, diagnostics redaction, storage safety, and low-RAM model fallback.

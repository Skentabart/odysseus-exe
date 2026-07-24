# Windows Native Troubleshooting

## Logs

Installed mode logs must be written under:

```text
%LOCALAPPDATA%\Odysseus\logs\
```

Portable mode logs must be written under:

```text
Odysseus-Portable\data\logs\
```

## Common startup issues

- If the UI opens before the backend is ready, the desktop shell should keep polling `/health` through `BackendLauncher.wait_for_health` and show a local status screen.
- If a local GGUF model cannot start, fall back to CPU mode or an external OpenAI-compatible provider instead of failing the whole app.
- If WebView2 is missing, the installer should install or bootstrap the WebView2 runtime.
- If a path contains spaces or Unicode characters, use the platform path layer rather than string concatenation.
- If diagnostics are exported, redact API keys, tokens, passwords, and secrets before zipping configuration files.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .paths import OdysseusPaths


@dataclass
class ModelConfig:
    provider: str = "external"
    model_path: str | None = None
    runtime: str = "llama.cpp"
    context_length: int = 4096
    gpu_layers: int = 0
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class AppConfig:
    backend_host: str = "127.0.0.1"
    backend_port: int = 7000
    ai: ModelConfig = field(default_factory=ModelConfig)
    storage_backend: str = "local"
    search_backend: str = "sqlite_fts5"
    mcp_servers: list[dict[str, Any]] = field(default_factory=list)


class ConfigStore:
    def __init__(self, paths: OdysseusPaths):
        self.path = paths.config / "config.json"

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        ai = ModelConfig(**payload.pop("ai", {}))
        return AppConfig(ai=ai, **payload)

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")


def redact_config(config_text: str) -> str:
    """Best-effort redaction for diagnostics exports; secrets belong in Credential Manager later."""
    sensitive = ("api_key", "apikey", "token", "secret", "password")
    try:
        data = json.loads(config_text)
    except json.JSONDecodeError:
        return config_text

    def redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: ("***REDACTED***" if any(s in k.lower() for s in sensitive) else redact(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [redact(v) for v in value]
        return value

    return json.dumps(redact(data), indent=2, ensure_ascii=False)

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .ai_runtime import AiRuntimeProcess, LlamaServerConfig, LlamaServerManager
from .backend_launcher import BackendLauncher, BackendProcess
from .config import AppConfig
from .logging_config import configure_logging
from .mcp import McpProcessManager, McpServerConfig
from .migrations import SQLiteMigrationRunner
from .models import ModelRegistry
from .paths import OdysseusPaths
from .search import SQLiteFtsSearch
from .storage import LocalStorage


@dataclass
class RuntimeStatus:
    data_root: str
    backend_url: str | None = None
    ai_url: str | None = None
    mcp_servers: list[str] = field(default_factory=list)
    search_backend: str = "sqlite_fts5"
    storage_backend: str = "local"


class WindowsNativeRuntime:
    """Coordinates native services without Docker for the desktop shell."""

    def __init__(self, paths: OdysseusPaths, config: AppConfig):
        self.paths = paths.ensure()
        self.config = config
        self.logger = configure_logging(paths)
        self.storage = LocalStorage(paths.data)
        self.search = SQLiteFtsSearch(paths.memory / "search.db")
        self.models = ModelRegistry(paths.models)
        self.migrations = SQLiteMigrationRunner(paths.database / "app.db")
        self.mcp = McpProcessManager(paths.logs)
        self.backend: BackendProcess | None = None
        self.ai_runtime: AiRuntimeProcess | None = None

    def initialize(self) -> list[int]:
        applied = self.migrations.apply()
        self.logger.info("Applied %s Windows-native migrations", len(applied))
        return [migration.version for migration in applied]

    def start_backend(self, module: str = "app", app: str = "app", python_exe: str | None = None) -> BackendProcess:
        launcher = BackendLauncher(self.config.backend_host, self.config.backend_port, self.paths.logs / "backend.log")
        self.backend = launcher.launch_module(module=module, app=app, python_exe=python_exe)
        return self.backend

    def start_ai_runtime(self, executable: Path, model_path: Path) -> AiRuntimeProcess:
        llama_config = LlamaServerConfig(
            executable=executable,
            model_path=model_path,
            context_length=self.config.ai.context_length,
            gpu_layers=self.config.ai.gpu_layers,
        )
        manager = LlamaServerManager(llama_config, self.paths.logs / "ai-runtime.log")
        self.ai_runtime = manager.start()
        return self.ai_runtime

    def start_mcp_servers(self) -> list[str]:
        started: list[str] = []
        for server in self.config.mcp_servers:
            process = self.mcp.start(
                McpServerConfig(
                    name=server["name"],
                    command=list(server["command"]),
                    cwd=Path(server["cwd"]) if server.get("cwd") else None,
                    env=dict(server.get("env", {})),
                )
            )
            started.append(process.name)
        return started

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            data_root=str(self.paths.root),
            backend_url=self.backend.url if self.backend else None,
            ai_url=self.ai_runtime.base_url if self.ai_runtime else None,
            mcp_servers=list(self.mcp._processes.keys()),
        )

    def shutdown(self) -> None:
        self.mcp.stop_all()
        if self.ai_runtime:
            self.ai_runtime.stop()
            self.ai_runtime = None
        if self.backend:
            self.backend.stop()
            self.backend = None
        self.logger.info("Windows-native runtime shutdown complete")

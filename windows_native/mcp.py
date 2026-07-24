from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class McpServerConfig:
    name: str
    command: list[str]
    cwd: Path | None = None
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class McpServerProcess:
    name: str
    process: subprocess.Popen

    def stop(self, timeout: float = 10.0) -> None:
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=timeout)


class McpProcessManager:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._processes: dict[str, McpServerProcess] = {}

    def start(self, config: McpServerConfig) -> McpServerProcess:
        if not config.command:
            raise ValueError("MCP server command must not be empty")
        if config.name in self._processes and self._processes[config.name].process.poll() is None:
            return self._processes[config.name]
        log_file = (self.log_dir / f"mcp-{config.name}.log").open("ab")
        process = subprocess.Popen(config.command, cwd=config.cwd, env=None if not config.env else config.env, stdout=log_file, stderr=subprocess.STDOUT)
        wrapped = McpServerProcess(name=config.name, process=process)
        self._processes[config.name] = wrapped
        return wrapped

    def stop_all(self) -> None:
        for process in list(self._processes.values()):
            process.stop()
        self._processes.clear()

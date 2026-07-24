from __future__ import annotations

import subprocess
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LlamaServerConfig:
    executable: Path
    model_path: Path
    host: str = "127.0.0.1"
    port: int = 8088
    context_length: int = 4096
    gpu_layers: int = 0
    threads: int | None = None

    def command(self) -> list[str]:
        cmd = [
            str(self.executable),
            "--model",
            str(self.model_path),
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--ctx-size",
            str(self.context_length),
            "--n-gpu-layers",
            str(self.gpu_layers),
        ]
        if self.threads is not None:
            cmd.extend(["--threads", str(self.threads)])
        return cmd


@dataclass
class AiRuntimeProcess:
    process: subprocess.Popen
    base_url: str

    def stop(self, timeout: float = 10.0) -> None:
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=timeout)


class LlamaServerManager:
    def __init__(self, config: LlamaServerConfig, log_file: Path | None = None):
        self.config = config
        self.log_file = log_file

    @property
    def health_url(self) -> str:
        return f"http://{self.config.host}:{self.config.port}/health"

    def validate(self) -> None:
        if not self.config.executable.exists():
            raise FileNotFoundError(f"llama-server executable not found: {self.config.executable}")
        if not self.config.model_path.exists():
            raise FileNotFoundError(f"GGUF model not found: {self.config.model_path}")

    def start(self) -> AiRuntimeProcess:
        self.validate()
        stdout = self.log_file.open("ab") if self.log_file else subprocess.DEVNULL
        process = subprocess.Popen(self.config.command(), stdout=stdout, stderr=subprocess.STDOUT)
        return AiRuntimeProcess(process=process, base_url=f"http://{self.config.host}:{self.config.port}")

    def wait_for_health(self, timeout: float = 60.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(self.health_url, timeout=1) as response:
                    if 200 <= response.status < 500:
                        return True
            except OSError:
                time.sleep(0.5)
        return False

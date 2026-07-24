from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BackendProcess:
    process: subprocess.Popen
    url: str

    def stop(self, timeout: float = 10.0) -> None:
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=timeout)


class BackendLauncher:
    def __init__(self, host: str = "127.0.0.1", port: int = 7000, log_file: Path | None = None):
        self.host = host
        self.port = port
        self.log_file = log_file

    @property
    def health_url(self) -> str:
        return f"http://{self.host}:{self.port}/health"

    def wait_for_health(self, timeout: float = 30.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(self.health_url, timeout=1) as response:
                    if 200 <= response.status < 300:
                        return True
            except OSError:
                time.sleep(0.25)
        return False

    def launch_module(self, module: str = "app", app: str = "app", python_exe: str | None = None) -> BackendProcess:
        exe = python_exe or sys.executable
        cmd = [exe, "-m", "uvicorn", f"{module}:{app}", "--host", self.host, "--port", str(self.port)]
        stdout = self.log_file.open("ab") if self.log_file else subprocess.DEVNULL
        process = subprocess.Popen(cmd, stdout=stdout, stderr=subprocess.STDOUT, cwd=Path.cwd())
        return BackendProcess(process=process, url=f"http://{self.host}:{self.port}")

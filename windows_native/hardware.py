from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class GpuInfo:
    name: str
    vendor: str = "Unknown"
    vram_gb: float | None = None


@dataclass(frozen=True)
class HardwareInfo:
    cpu: str
    ram_gb: float | None
    gpus: tuple[GpuInfo, ...]
    cuda_available: bool = False


def _detect_ram_gb() -> float | None:
    if hasattr(os, "sysconf"):
        try:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3)
        except (ValueError, OSError):
            return None
    return None


def _detect_windows_gpus() -> tuple[GpuInfo, ...]:
    if platform.system().lower() != "windows" or not shutil.which("powershell"):
        return ()
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json -Compress",
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return ()
    if completed.returncode != 0 or not completed.stdout.strip():
        return ()
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return ()
    rows = payload if isinstance(payload, list) else [payload]
    gpus: list[GpuInfo] = []
    for row in rows:
        name = str(row.get("Name") or "Unknown GPU")
        vendor = "NVIDIA" if "nvidia" in name.lower() else "AMD" if "amd" in name.lower() or "radeon" in name.lower() else "Intel" if "intel" in name.lower() else "Unknown"
        adapter_ram = row.get("AdapterRAM")
        vram_gb = float(adapter_ram) / (1024**3) if isinstance(adapter_ram, int) and adapter_ram > 0 else None
        gpus.append(GpuInfo(name=name, vendor=vendor, vram_gb=vram_gb))
    return tuple(gpus)


def _detect_cuda() -> bool:
    return shutil.which("nvidia-smi") is not None


def detect_hardware() -> HardwareInfo:
    return HardwareInfo(
        cpu=platform.processor() or platform.machine(),
        ram_gb=_detect_ram_gb(),
        gpus=_detect_windows_gpus(),
        cuda_available=_detect_cuda(),
    )


def recommended_models(info: HardwareInfo) -> list[str]:
    ram = info.ram_gb or 0
    best_vram = max((gpu.vram_gb or 0 for gpu in info.gpus), default=0)
    if best_vram >= 16 and ram >= 32:
        return ["14B Q4_K_M with GPU", "7B Q5_K_M with GPU", "7B Q4_K_M"]
    if best_vram >= 8 and ram >= 16:
        return ["7B Q4_K_M with GPU", "3B Q5_K_M"]
    if ram >= 48:
        return ["14B Q4_K_M CPU", "7B Q5_K_M", "7B Q4_K_M"]
    if ram >= 16:
        return ["7B Q4_K_M", "3B Q5_K_M"]
    return ["3B Q4_K_M", "External API provider"]

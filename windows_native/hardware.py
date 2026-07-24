from __future__ import annotations

import os
import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareInfo:
    cpu: str
    ram_gb: float | None
    gpus: tuple[str, ...]


def detect_hardware() -> HardwareInfo:
    ram_gb = None
    if hasattr(os, "sysconf"):
        try:
            ram_gb = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3)
        except (ValueError, OSError):
            ram_gb = None
    return HardwareInfo(cpu=platform.processor() or platform.machine(), ram_gb=ram_gb, gpus=())


def recommended_models(info: HardwareInfo) -> list[str]:
    ram = info.ram_gb or 0
    if ram >= 48:
        return ["14B Q4_K_M", "7B Q5_K_M", "7B Q4_K_M"]
    if ram >= 16:
        return ["7B Q4_K_M", "3B Q5_K_M"]
    return ["3B Q4_K_M", "External API provider"]

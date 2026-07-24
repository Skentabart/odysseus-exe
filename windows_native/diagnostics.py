from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .config import redact_config
from .paths import OdysseusPaths


def export_diagnostics(paths: OdysseusPaths, destination: Path | None = None) -> Path:
    """Create a diagnostics ZIP without copying model/user document payloads or plaintext secrets."""
    paths.ensure()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = destination or paths.logs / f"odysseus-diagnostics-{timestamp}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "created_utc": timestamp,
        "portable": paths.portable,
        "included": ["config/config.redacted.json", "logs/*.log", "manifest.json"],
        "excluded": ["models", "documents", "uploads", "memory", "cache"],
    }

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        config_file = paths.config / "config.json"
        if config_file.exists():
            archive.writestr("config/config.redacted.json", redact_config(config_file.read_text(encoding="utf-8")))
        for log_file in sorted(paths.logs.glob("*.log")):
            archive.write(log_file, arcname=f"logs/{log_file.name}")
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    return output

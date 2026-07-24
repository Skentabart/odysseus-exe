from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "Odysseus"
PORTABLE_MARKER = "odysseus.portable"


@dataclass(frozen=True)
class OdysseusPaths:
    root: Path
    config: Path
    data: Path
    database: Path
    documents: Path
    uploads: Path
    memory: Path
    models: Path
    logs: Path
    cache: Path
    portable: bool

    def ensure(self) -> "OdysseusPaths":
        for path in (
            self.config,
            self.data,
            self.database,
            self.documents,
            self.uploads,
            self.memory,
            self.models,
            self.logs,
            self.cache,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return self


def _default_local_app_data() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data)
    return Path.home() / "AppData" / "Local"


def resolve_paths(app_dir: str | os.PathLike[str] | None = None, portable: bool | None = None) -> OdysseusPaths:
    r"""Resolve installed or portable Odysseus data paths without hard-coded separators.

    Portable mode is selected explicitly or by placing an `odysseus.portable` marker next to
    `Odysseus.exe`/the application directory. Installed mode stores user data under
    `%LOCALAPPDATA%\Odysseus` and never inside Program Files.
    """
    base_dir = Path(app_dir).resolve() if app_dir else Path.cwd().resolve()
    is_portable = portable if portable is not None else (base_dir / PORTABLE_MARKER).exists()
    root = base_dir / "data" if is_portable else _default_local_app_data() / APP_NAME
    return OdysseusPaths(
        root=root,
        config=root / "config",
        data=root / "data",
        database=root / "database",
        documents=root / "documents",
        uploads=root / "uploads",
        memory=root / "memory",
        models=root / "models",
        logs=root / "logs",
        cache=root / "cache",
        portable=is_portable,
    )

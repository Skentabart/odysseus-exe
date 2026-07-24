from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath


class StorageBackend(ABC):
    @abstractmethod
    def write_bytes(self, key: str, data: bytes) -> Path | str: ...

    @abstractmethod
    def read_bytes(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalStorage(StorageBackend):
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        normalized = PurePosixPath(key.replace("\\", "/"))
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError(f"Unsafe storage key: {key!r}")
        path = (self.root / Path(*normalized.parts)).resolve()
        if self.root not in path.parents and path != self.root:
            raise ValueError(f"Storage key escapes root: {key!r}")
        return path

    def write_bytes(self, key: str, data: bytes) -> Path:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class LocalModel:
    name: str
    path: Path
    size_bytes: int
    format: str = "GGUF"

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024**3)

    def to_dict(self) -> dict[str, str | int | float]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        payload["size_gb"] = round(self.size_gb, 3)
        return payload


class ModelRegistry:
    """Local GGUF model registry rooted in the Windows-native user data directory."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def list_models(self) -> list[LocalModel]:
        models: list[LocalModel] = []
        for path in sorted(self.models_dir.rglob("*.gguf")):
            if path.is_file():
                models.append(LocalModel(name=path.stem, path=path, size_bytes=path.stat().st_size))
        return models

    def resolve_existing(self, path: str | Path) -> LocalModel:
        model_path = Path(path).expanduser().resolve()
        if not model_path.exists() or not model_path.is_file():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if model_path.suffix.lower() != ".gguf":
            raise ValueError(f"Only GGUF models are supported by the native runtime: {model_path}")
        return LocalModel(name=model_path.stem, path=model_path, size_bytes=model_path.stat().st_size)

    def delete_model(self, path: str | Path) -> None:
        model = self.resolve_existing(path)
        try:
            model.path.relative_to(self.models_dir.resolve())
        except ValueError as exc:
            raise ValueError("Refusing to delete a model outside the managed models directory") from exc
        model.path.unlink()

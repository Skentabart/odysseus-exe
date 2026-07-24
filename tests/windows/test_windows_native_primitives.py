import json

import pytest

from windows_native.config import AppConfig, ConfigStore, redact_config
from windows_native.hardware import HardwareInfo, recommended_models
from windows_native.paths import resolve_paths
from windows_native.storage import LocalStorage


def test_installed_paths_use_localappdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    paths = resolve_paths(app_dir=tmp_path / "Program Files" / "Odysseus", portable=False).ensure()
    assert paths.root == tmp_path / "LocalAppData" / "Odysseus"
    assert paths.database.exists()
    assert not paths.portable


def test_portable_paths_stay_next_to_app(tmp_path):
    app_dir = tmp_path / "Odysseus Portable"
    app_dir.mkdir()
    paths = resolve_paths(app_dir=app_dir, portable=True).ensure()
    assert paths.root == app_dir / "data"
    assert paths.models.exists()
    assert paths.portable


def test_config_roundtrip_handles_unicode_and_spaces(tmp_path):
    paths = resolve_paths(app_dir=tmp_path / "Пример App", portable=True).ensure()
    store = ConfigStore(paths)
    config = AppConfig(backend_port=7766)
    config.ai.model_path = str(paths.models / "модель 7b.gguf")
    store.save(config)
    assert store.load().ai.model_path.endswith("модель 7b.gguf")
    assert store.load().backend_port == 7766


def test_diagnostics_redacts_secret_like_keys():
    redacted = redact_config(json.dumps({"api_key": "abc", "nested": {"password": "pw", "safe": "ok"}}))
    assert "abc" not in redacted
    assert "pw" not in redacted
    assert "ok" in redacted


def test_local_storage_blocks_path_traversal(tmp_path):
    storage = LocalStorage(tmp_path / "data")
    storage.write_bytes("documents/hello.txt", "hello".encode("utf-8"))
    assert storage.read_bytes("documents/hello.txt") == b"hello"
    with pytest.raises(ValueError):
        storage.write_bytes("../escape.txt", b"no")


def test_model_recommendations_include_low_ram_fallback():
    assert "External API provider" in recommended_models(HardwareInfo(cpu="x64", ram_gb=8, gpus=()))

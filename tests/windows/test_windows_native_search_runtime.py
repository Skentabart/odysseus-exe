import json
import sys

import pytest

from windows_native.ai_runtime import LlamaServerConfig, LlamaServerManager
from windows_native.diagnostics import export_diagnostics
from windows_native.hardware import GpuInfo, HardwareInfo, recommended_models
from windows_native.mcp import McpProcessManager, McpServerConfig
from windows_native.models import ModelRegistry
from windows_native.paths import resolve_paths
from windows_native.search import SQLiteFtsSearch


def test_sqlite_fts_search_indexes_unicode_content(tmp_path):
    search = SQLiteFtsSearch(tmp_path / "memory" / "search.db")
    search.upsert_document("doc-1", "Odysseus", "Локальная модель GGUF работает без Docker")
    results = search.search("GGUF")
    assert results[0].key == "doc-1"
    assert "GGUF" in results[0].snippet


def test_diagnostics_export_redacts_config_and_excludes_documents(tmp_path):
    paths = resolve_paths(app_dir=tmp_path, portable=True).ensure()
    (paths.config / "config.json").write_text(json.dumps({"api_key": "secret", "safe": "ok"}), encoding="utf-8")
    (paths.logs / "backend.log").write_text("started", encoding="utf-8")
    (paths.documents / "private.txt").write_text("do not include", encoding="utf-8")
    archive = export_diagnostics(paths)
    import zipfile
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        assert "config/config.redacted.json" in names
        assert "logs/backend.log" in names
        assert "documents/private.txt" not in names
        assert "secret" not in zf.read("config/config.redacted.json").decode("utf-8")


def test_llama_server_command_uses_loopback_and_model_path(tmp_path):
    exe = tmp_path / "llama-server.exe"
    model = tmp_path / "models" / "model.gguf"
    exe.write_text("", encoding="utf-8")
    model.parent.mkdir()
    model.write_text("", encoding="utf-8")
    config = LlamaServerConfig(executable=exe, model_path=model, gpu_layers=12, context_length=8192)
    assert "127.0.0.1" in config.command()
    assert str(model) in config.command()
    LlamaServerManager(config).validate()


def test_llama_server_validate_rejects_missing_model(tmp_path):
    exe = tmp_path / "llama-server.exe"
    exe.write_text("", encoding="utf-8")
    manager = LlamaServerManager(LlamaServerConfig(executable=exe, model_path=tmp_path / "missing.gguf"))
    with pytest.raises(FileNotFoundError):
        manager.validate()


def test_mcp_process_manager_starts_and_stops_local_process(tmp_path):
    manager = McpProcessManager(tmp_path / "logs")
    proc = manager.start(McpServerConfig(name="noop", command=[sys.executable, "-c", "import time; time.sleep(30)"]))
    assert proc.process.poll() is None
    manager.stop_all()
    assert proc.process.poll() is not None


def test_model_registry_lists_and_deletes_managed_gguf(tmp_path):
    registry = ModelRegistry(tmp_path / "models")
    model_path = registry.models_dir / "tiny.gguf"
    model_path.write_bytes(b"gguf")
    models = registry.list_models()
    assert models[0].name == "tiny"
    assert models[0].size_bytes == 4
    registry.delete_model(model_path)
    assert registry.list_models() == []


def test_model_registry_refuses_non_gguf(tmp_path):
    registry = ModelRegistry(tmp_path / "models")
    bad = registry.models_dir / "model.bin"
    bad.write_bytes(b"bin")
    with pytest.raises(ValueError):
        registry.resolve_existing(bad)


def test_gpu_recommendations_prefer_gpu_when_vram_available():
    info = HardwareInfo(cpu="x64", ram_gb=32, gpus=(GpuInfo(name="NVIDIA RTX", vendor="NVIDIA", vram_gb=12),), cuda_available=True)
    assert recommended_models(info)[0].endswith("with GPU")

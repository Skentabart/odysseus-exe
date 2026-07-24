import json
import subprocess
import sys
import zipfile


def test_cli_init_creates_config_in_portable_dir(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "windows_native", "--app-dir", str(tmp_path), "--portable", "init"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["portable"] is True
    assert (tmp_path / "data" / "config" / "config.json").exists()


def test_cli_list_models_outputs_managed_gguf(tmp_path):
    model_dir = tmp_path / "data" / "models"
    model_dir.mkdir(parents=True)
    (model_dir / "tiny.gguf").write_bytes(b"gguf")
    result = subprocess.run(
        [sys.executable, "-m", "windows_native", "--app-dir", str(tmp_path), "--portable", "list-models"],
        check=True,
        capture_output=True,
        text=True,
    )
    models = json.loads(result.stdout)
    assert models[0]["name"] == "tiny"


def test_cli_export_diagnostics_creates_redacted_zip(tmp_path):
    config = tmp_path / "data" / "config"
    config.mkdir(parents=True)
    (config / "config.json").write_text('{"api_key":"secret"}', encoding="utf-8")
    output = tmp_path / "diag.zip"
    subprocess.run(
        [sys.executable, "-m", "windows_native", "--app-dir", str(tmp_path), "--portable", "export-diagnostics", "--output", str(output)],
        check=True,
    )
    with zipfile.ZipFile(output) as archive:
        assert "secret" not in archive.read("config/config.redacted.json").decode("utf-8")

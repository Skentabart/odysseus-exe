import logging
import sqlite3

from windows_native.config import AppConfig
from windows_native.logging_config import configure_logging
from windows_native.migrations import Migration, SQLiteMigrationRunner
from windows_native.orchestrator import WindowsNativeRuntime
from windows_native.paths import resolve_paths


def test_migration_runner_applies_each_migration_once(tmp_path):
    db = tmp_path / "database" / "app.db"
    runner = SQLiteMigrationRunner(db, (Migration(1, "one", "CREATE TABLE sample(id INTEGER PRIMARY KEY);") ,))
    assert [migration.version for migration in runner.apply()] == [1]
    assert runner.apply() == []
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='sample'").fetchone()


def test_logging_writes_to_native_logs_dir(tmp_path):
    paths = resolve_paths(app_dir=tmp_path, portable=True).ensure()
    logger = configure_logging(paths, "test-log")
    logger.info("hello")
    for handler in logger.handlers:
        handler.flush()
    assert "hello" in (paths.logs / "test-log.log").read_text(encoding="utf-8")
    logger.setLevel(logging.INFO)


def test_runtime_initializes_storage_search_and_migrations(tmp_path):
    paths = resolve_paths(app_dir=tmp_path, portable=True)
    runtime = WindowsNativeRuntime(paths, AppConfig())
    applied = runtime.initialize()
    assert applied == [1, 2]
    runtime.storage.write_bytes("documents/a.txt", b"alpha")
    runtime.search.upsert_document("a", "Alpha", "Odysseus native runtime")
    assert runtime.search.search("Odysseus")[0].key == "a"
    assert runtime.status().data_root == str(paths.root)
    runtime.shutdown()

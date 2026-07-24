from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


DEFAULT_MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        1,
        "windows_native_metadata",
        """
        CREATE TABLE IF NOT EXISTS windows_native_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """,
    ),
    Migration(
        2,
        "managed_models",
        """
        CREATE TABLE IF NOT EXISTS managed_models (
            path TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
)


class SQLiteMigrationRunner:
    def __init__(self, database_path: Path, migrations: tuple[Migration, ...] = DEFAULT_MIGRATIONS):
        self.database_path = database_path
        self.migrations = tuple(sorted(migrations, key=lambda migration: migration.version))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def apply(self) -> list[Migration]:
        applied: list[Migration] = []
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            existing = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
            for migration in self.migrations:
                if migration.version in existing:
                    continue
                connection.executescript(migration.sql)
                connection.execute(
                    "INSERT INTO schema_migrations(version, name) VALUES (?, ?)",
                    (migration.version, migration.name),
                )
                applied.append(migration)
            connection.commit()
        return applied

    def applied_versions(self) -> list[int]:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            return [row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchResult:
    key: str
    title: str
    snippet: str
    score: float


class SQLiteFtsSearch:
    """Embedded SQLite FTS5 search backend for Windows-native MVP."""

    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
                USING fts5(key UNINDEXED, title, body, tokenize='unicode61')
                """
            )
            connection.commit()

    def upsert_document(self, key: str, title: str, body: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM documents_fts WHERE key = ?", (key,))
            connection.execute(
                "INSERT INTO documents_fts(key, title, body) VALUES (?, ?, ?)",
                (key, title, body),
            )
            connection.commit()

    def delete_document(self, key: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM documents_fts WHERE key = ?", (key,))
            connection.commit()

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not query.strip():
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT key, title,
                       snippet(documents_fts, 2, '[', ']', '…', 12) AS snippet,
                       bm25(documents_fts) AS score
                FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [
            SearchResult(key=row["key"], title=row["title"], snippet=row["snippet"], score=float(row["score"]))
            for row in rows
        ]

"""SQLite access for the Polls website."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    label TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 100),
    position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    option_id INTEGER NOT NULL REFERENCES options(id),
    voter_token TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (poll_id, voter_token)
);
"""


class Database:
    """Opens short-lived SQLite connections to one database file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def ensure_schema(self) -> None:
        """Create the tables when they do not exist yet."""
        conn = self.connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        conn = self.connect()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection inside one transaction; commit on success, roll back on error."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

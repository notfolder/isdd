"""SQLite connection and schema for polls, options and votes."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL CHECK (length(question) BETWEEN 1 AND 200),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 500),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    label TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 100),
    position INTEGER NOT NULL CHECK (position >= 1),
    UNIQUE (poll_id, label)
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    option_id INTEGER NOT NULL REFERENCES options(id),
    voter_id TEXT NOT NULL CHECK (length(voter_id) = 32),
    voted_at TEXT NOT NULL,
    UNIQUE (poll_id, voter_id)
);
"""


def open_database(db_path: Path) -> sqlite3.Connection:
    """Open the SQLite file in autocommit mode with foreign keys enabled and rows as mappings."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create the polls, options and votes tables if they do not exist."""
    conn.executescript(SCHEMA)

"""SQLite connection handling and schema creation for the polls site."""
import sqlite3
from pathlib import Path

DB_FILE_NAME = "polls.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT
);
CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    text TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE (poll_id, position)
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    option_id INTEGER NOT NULL REFERENCES options(id),
    voter_token TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (poll_id, voter_token)
);
"""


def get_db(data_dir):
    """Open the SQLite database under data_dir, creating the directory if needed.

    Rows are returned as sqlite3.Row objects and foreign keys are enforced.
    The caller closes the connection.
    """
    directory = Path(data_dir)
    directory.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(directory / DB_FILE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Create the polls, options and votes tables when they do not exist yet."""
    conn.executescript(SCHEMA)
    conn.commit()

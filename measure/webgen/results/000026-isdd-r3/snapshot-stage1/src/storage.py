"""SQLite storage for poll questions, options and votes (standard library only)."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_FILE_NAME = "polls.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL CHECK (length(question) BETWEEN 1 AND 200)
);
CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    text TEXT NOT NULL CHECK (length(text) BETWEEN 1 AND 100),
    position INTEGER NOT NULL,
    UNIQUE (poll_id, position)
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_id INTEGER NOT NULL REFERENCES options(id),
    created_at TEXT NOT NULL
);
"""

# Sample polls used when the database has no polls yet.
# Each option has an initial number of votes.
SAMPLE_POLLS = [
    {
        "question": "What is your favourite programming language?",
        "options": [("Python", 12), ("JavaScript", 9), ("Go", 5), ("Rust", 3)],
    },
    {
        "question": "Which season do you like best?",
        "options": [("Spring", 7), ("Summer", 10), ("Autumn", 4), ("Winter", 2)],
    },
    {
        "question": "Where should we hold the team lunch?",
        "options": [("Italian", 6), ("Japanese", 8), ("Mexican", 3)],
    },
]


def open_database(data_dir):
    """Open (and create if needed) the SQLite database under data_dir.

    Creates data_dir, the schema, and the sample data when no poll exists.
    Returns an open sqlite3 connection.
    """
    directory = Path(data_dir)
    directory.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(directory / DB_FILE_NAME))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    seed_sample_data(conn)
    return conn


def seed_sample_data(conn):
    """Insert the sample polls, options and votes when there are no polls.

    Runs in one transaction. Does nothing when at least one poll exists.
    """
    count = conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0]
    if count > 0:
        return
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        for sample in SAMPLE_POLLS:
            poll_id = conn.execute(
                "INSERT INTO polls (question) VALUES (?)", (sample["question"],)
            ).lastrowid
            for position, (text, initial_votes) in enumerate(sample["options"], start=1):
                option_id = conn.execute(
                    "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                    (poll_id, text, position),
                ).lastrowid
                conn.executemany(
                    "INSERT INTO votes (option_id, created_at) VALUES (?, ?)",
                    [(option_id, now)] * initial_votes,
                )


def list_polls_with_totals(conn):
    """Return every poll with its option count and total votes, ordered by id.

    Each item is a dict with keys id, question, option_count, total_votes.
    """
    rows = conn.execute(
        """
        SELECT p.id, p.question,
               (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count,
               (SELECT COUNT(*) FROM votes v
                  JOIN options o ON v.option_id = o.id
                 WHERE o.poll_id = p.id) AS total_votes
          FROM polls p
         ORDER BY p.id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def find_poll(conn, poll_id):
    """Return the poll with the given id as a dict (id, question), or None."""
    row = conn.execute(
        "SELECT id, question FROM polls WHERE id = ?", (poll_id,)
    ).fetchone()
    return dict(row) if row is not None else None


def list_options_with_counts(conn, poll_id):
    """Return the options of a poll in display order with their vote counts.

    Each item is a dict with keys id, text, votes.
    """
    rows = conn.execute(
        """
        SELECT o.id, o.text, COUNT(v.id) AS votes
          FROM options o
          LEFT JOIN votes v ON v.option_id = o.id
         WHERE o.poll_id = ?
         GROUP BY o.id, o.text, o.position
         ORDER BY o.position
        """,
        (poll_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def find_option(conn, poll_id, option_id):
    """Return the option if it belongs to the poll (dict id, text), or None."""
    row = conn.execute(
        "SELECT id, text FROM options WHERE id = ? AND poll_id = ?",
        (option_id, poll_id),
    ).fetchone()
    return dict(row) if row is not None else None


def insert_vote(conn, option_id):
    """Record one vote for the option and commit."""
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute(
            "INSERT INTO votes (option_id, created_at) VALUES (?, ?)",
            (option_id, now),
        )

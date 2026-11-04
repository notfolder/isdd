"""SQL access for polls, options and votes. Transactions are controlled by the caller."""

import sqlite3
from typing import Any, Optional


class PollRepository:
    """Reads and writes polls, options and votes through one SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_poll(self, question: str, description: str, created_at: str) -> int:
        """Insert a poll and return its id."""
        cur = self.conn.execute(
            "INSERT INTO polls (question, description, created_at) VALUES (?, ?, ?)",
            (question, description, created_at),
        )
        return int(cur.lastrowid)

    def insert_option(self, poll_id: int, label: str, position: int) -> int:
        """Insert an option of a poll and return its id."""
        cur = self.conn.execute(
            "INSERT INTO options (poll_id, label, position) VALUES (?, ?, ?)",
            (poll_id, label, position),
        )
        return int(cur.lastrowid)

    def count_polls(self) -> int:
        """Return the number of polls."""
        return int(self.conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0])

    def list_polls(self) -> list[dict[str, Any]]:
        """Return all polls in id order with their option counts."""
        rows = self.conn.execute(
            """SELECT p.id, p.question, p.description,
                      (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count
               FROM polls p ORDER BY p.id"""
        ).fetchall()
        return [dict(r) for r in rows]

    def get_poll(self, poll_id: int) -> Optional[dict[str, Any]]:
        """Return one poll by id, or None when it does not exist."""
        row = self.conn.execute(
            "SELECT id, question, description FROM polls WHERE id = ?", (poll_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_options(self, poll_id: int) -> list[dict[str, Any]]:
        """Return the options of a poll in display order."""
        rows = self.conn.execute(
            "SELECT id, poll_id, label, position FROM options WHERE poll_id = ? ORDER BY position, id",
            (poll_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_option(self, option_id: int) -> Optional[dict[str, Any]]:
        """Return one option by id, or None when it does not exist."""
        row = self.conn.execute(
            "SELECT id, poll_id, label, position FROM options WHERE id = ?", (option_id,)
        ).fetchone()
        return dict(row) if row else None

    def find_vote(self, poll_id: int, voter_id: str) -> Optional[dict[str, Any]]:
        """Return the vote of this voter in this poll, or None."""
        row = self.conn.execute(
            "SELECT id, poll_id, option_id, voter_id, voted_at FROM votes WHERE poll_id = ? AND voter_id = ?",
            (poll_id, voter_id),
        ).fetchone()
        return dict(row) if row else None

    def insert_vote(self, poll_id: int, option_id: int, voter_id: str, voted_at: str) -> bool:
        """Insert a vote. Return False when this voter has already voted in this poll (unique constraint)."""
        try:
            self.conn.execute(
                "INSERT INTO votes (poll_id, option_id, voter_id, voted_at) VALUES (?, ?, ?, ?)",
                (poll_id, option_id, voter_id, voted_at),
            )
        except sqlite3.IntegrityError:
            return False
        return True

    def count_votes_by_option(self, poll_id: int) -> dict[int, int]:
        """Return the number of votes per option id for a poll (options without votes are absent)."""
        rows = self.conn.execute(
            "SELECT option_id, COUNT(*) AS n FROM votes WHERE poll_id = ? GROUP BY option_id",
            (poll_id,),
        ).fetchall()
        return {int(r["option_id"]): int(r["n"]) for r in rows}

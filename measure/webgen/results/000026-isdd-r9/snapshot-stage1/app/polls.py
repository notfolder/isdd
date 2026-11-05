"""Business logic for polls: listing, voting, and counting results."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from db import Database

VOTE_OK = "ok"
VOTE_NOT_FOUND = "not_found"
VOTE_NO_OPTION = "no_option"
VOTE_INVALID_OPTION = "invalid_option"
VOTE_ALREADY_VOTED = "already_voted"


class PollService:
    """Reads polls and records votes. One vote per poll per voter token."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def list_polls(self) -> list[dict[str, Any]]:
        rows = self._db.query(
            """
            SELECT p.id, p.title, p.description,
                   (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count,
                   (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total_votes
            FROM polls p
            ORDER BY p.id
            """
        )
        return [dict(row) for row in rows]

    def get_poll(self, poll_id: int) -> dict[str, Any] | None:
        polls = self._db.query("SELECT id, title, description FROM polls WHERE id = ?", (poll_id,))
        if not polls:
            return None
        poll = dict(polls[0])
        options = self._db.query(
            "SELECT id, label FROM options WHERE poll_id = ? ORDER BY position, id", (poll_id,)
        )
        poll["options"] = [dict(row) for row in options]
        return poll

    def cast_vote(self, poll_id: int, option_id: int | None, voter_token: str) -> str:
        """Record a vote and return one of the VOTE_* results. Nothing is stored unless the result is VOTE_OK."""
        with self._db.transaction() as conn:
            if conn.execute("SELECT 1 FROM polls WHERE id = ?", (poll_id,)).fetchone() is None:
                return VOTE_NOT_FOUND
            if option_id is None:
                return VOTE_NO_OPTION
            option = conn.execute(
                "SELECT id FROM options WHERE id = ? AND poll_id = ?", (option_id, poll_id)
            ).fetchone()
            if option is None:
                return VOTE_INVALID_OPTION
            already = conn.execute(
                "SELECT 1 FROM votes WHERE poll_id = ? AND voter_token = ?", (poll_id, voter_token)
            ).fetchone()
            if already is not None:
                return VOTE_ALREADY_VOTED
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            try:
                conn.execute(
                    "INSERT INTO votes (poll_id, option_id, voter_token, created_at) VALUES (?, ?, ?, ?)",
                    (poll_id, option_id, voter_token, now),
                )
            except sqlite3.IntegrityError:
                # A concurrent request from the same voter won the race for the unique key.
                return VOTE_ALREADY_VOTED
            return VOTE_OK

    def get_results(self, poll_id: int) -> dict[str, Any] | None:
        poll = self.get_poll(poll_id)
        if poll is None:
            return None
        rows = self._db.query(
            """
            SELECT o.id, o.label, COUNT(v.id) AS votes
            FROM options o
            LEFT JOIN votes v ON v.option_id = o.id
            WHERE o.poll_id = ?
            GROUP BY o.id
            ORDER BY o.position, o.id
            """,
            (poll_id,),
        )
        total = sum(row["votes"] for row in rows)
        options = []
        for row in rows:
            percent = round(row["votes"] * 100 / total, 1) if total else 0.0
            options.append({"id": row["id"], "label": row["label"], "votes": row["votes"], "percent": percent})
        return {"poll": poll, "total_votes": total, "options": options}

    def list_results(self) -> list[dict[str, Any]]:
        rows = self._db.query(
            """
            SELECT p.id, p.title,
                   (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total_votes
            FROM polls p
            ORDER BY p.id
            """
        )
        return [dict(row) for row in rows]

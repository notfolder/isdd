"""Sample content for an empty database, so every feature can be tried at once."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from db import Database

SAMPLE_POLLS = [
    {
        "title": "Favorite season?",
        "description": "Pick the season you enjoy most.",
        "options": {"Spring": 3, "Summer": 5, "Autumn": 2, "Winter": 1},
    },
    {
        "title": "Best programming language for beginners?",
        "description": "Which language would you recommend to a new learner?",
        "options": {"Python": 0, "JavaScript": 0, "Java": 0},
    },
    {
        "title": "Preferred lunch?",
        "description": "Choose your usual lunch.",
        "options": {"Rice bowl": 2, "Noodles": 4, "Sandwich": 1},
    },
]


class SampleSeeder:
    """Inserts the sample polls when the poll table is empty."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def seed_if_empty(self) -> bool:
        """Return True when sample data was inserted, False when polls already exist."""
        if self._db.query("SELECT COUNT(*) AS n FROM polls")[0]["n"] > 0:
            return False
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._db.transaction() as conn:
            for poll in SAMPLE_POLLS:
                cur = conn.execute(
                    "INSERT INTO polls (title, description, created_at) VALUES (?, ?, ?)",
                    (poll["title"], poll["description"], now),
                )
                poll_id = cur.lastrowid
                option_ids: dict[str, int] = {}
                for position, label in enumerate(poll["options"], start=1):
                    opt = conn.execute(
                        "INSERT INTO options (poll_id, label, position) VALUES (?, ?, ?)",
                        (poll_id, label, position),
                    )
                    option_ids[label] = opt.lastrowid
                for label, count in poll["options"].items():
                    for _ in range(count):
                        conn.execute(
                            "INSERT INTO votes (poll_id, option_id, voter_token, created_at) "
                            "VALUES (?, ?, ?, ?)",
                            (poll_id, option_ids[label], secrets.token_hex(16), now),
                        )
        return True

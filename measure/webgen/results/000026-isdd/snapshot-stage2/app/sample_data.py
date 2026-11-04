"""Sample polls, options and votes that are added when the database has no polls."""

import sqlite3
from datetime import datetime, timezone

from .repository import PollRepository

SAMPLE_POLLS = [
    {
        "question": "Which programming language do you like most?",
        "description": "Pick one language.",
        "options": [("Python", 5), ("JavaScript", 3), ("Go", 1), ("Rust", 2)],
    },
    {
        "question": "Where should we hold the team lunch?",
        "description": "The team will vote once.",
        "options": [("Cafeteria", 2), ("Nearby ramen shop", 4), ("Bring your own bento", 1)],
    },
    {
        "question": "Which season is your favorite?",
        "description": "",
        "options": [("Spring", 3), ("Summer", 1), ("Autumn", 2), ("Winter", 0)],
    },
]


def seed_sample_data(conn: sqlite3.Connection) -> bool:
    """Insert the sample polls, options and votes when there are no polls. Return True if data was added."""
    repo = PollRepository(conn)
    if repo.count_polls() > 0:
        return False
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    voter_number = 0
    conn.execute("BEGIN IMMEDIATE")
    try:
        for sample in SAMPLE_POLLS:
            poll_id = repo.insert_poll(sample["question"], sample["description"], now)
            for position, (label, votes) in enumerate(sample["options"], start=1):
                option_id = repo.insert_option(poll_id, label, position)
                for _ in range(votes):
                    voter_number += 1
                    repo.insert_vote(poll_id, option_id, f"{voter_number:032x}", now)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return True

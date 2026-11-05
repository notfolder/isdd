"""Sample polls that are loaded on first start when the database has no polls."""
import hashlib
from datetime import datetime, timezone

SAMPLE_POLLS = [
    {
        "title": "Which programming language do you prefer?",
        "description": "Choose the language you use most often.",
        "options": [("Python", 5), ("JavaScript", 3), ("Go", 1), ("Rust", 2)],
    },
    {
        "title": "Best day for the team meeting?",
        "description": "Pick the day that works best for you.",
        "options": [("Monday", 2), ("Wednesday", 4), ("Friday", 1)],
    },
    {
        "title": "Where should we have lunch?",
        "description": "Vote for your favorite lunch spot.",
        "options": [("Noodle bar", 3), ("Sandwich shop", 1), ("Cafeteria", 2), ("Food truck", 1)],
    },
]


def _sample_token(poll_key, vote_index):
    """Return a deterministic 32-character token so that sample votes never collide."""
    return hashlib.sha256(f"sample-{poll_key}-{vote_index}".encode("utf-8")).hexdigest()[:32]


def seed_sample_data(conn):
    """Insert the sample polls, options and votes when no poll exists yet.

    Returns True when the sample data was inserted and False when the database already had polls.
    """
    existing = conn.execute("SELECT COUNT(*) FROM polls").fetchone()[0]
    if existing:
        return False
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    vote_index = 0
    for poll_number, sample in enumerate(SAMPLE_POLLS, start=1):
        cursor = conn.execute(
            "INSERT INTO polls (title, description) VALUES (?, ?)",
            (sample["title"], sample["description"]),
        )
        poll_id = cursor.lastrowid
        for position, (text, votes) in enumerate(sample["options"]):
            option_cursor = conn.execute(
                "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                (poll_id, text, position),
            )
            option_id = option_cursor.lastrowid
            for _ in range(votes):
                vote_index += 1
                conn.execute(
                    "INSERT INTO votes (poll_id, option_id, voter_token, created_at) VALUES (?, ?, ?, ?)",
                    (poll_id, option_id, _sample_token(poll_number, vote_index), created_at),
                )
    conn.commit()
    return True

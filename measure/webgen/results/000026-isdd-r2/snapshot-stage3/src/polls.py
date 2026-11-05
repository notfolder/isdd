"""Poll reading, vote recording and result aggregation.

Every function receives an open sqlite3 connection and does not manage it.
"""
import sqlite3
from datetime import datetime, timezone

NOT_SELECTED = "not_selected"
INVALID_OPTION = "invalid_option"
ALREADY_VOTED = "already_voted"

MESSAGES = {
    NOT_SELECTED: "Please select an option before voting.",
    INVALID_OPTION: "The selected option is not valid for this survey.",
    ALREADY_VOTED: "You have already voted in this survey.",
}


class VoteError(Exception):
    """A vote was not recorded. code is one of not_selected, invalid_option or already_voted."""

    def __init__(self, code):
        super().__init__(MESSAGES[code])
        self.code = code
        self.message = MESSAGES[code]


def _percent(votes, total):
    """Return the share of votes in percent, rounded to one decimal place (0.0 when there are no votes)."""
    if total == 0:
        return 0.0
    return round(votes * 100 / total, 1)


def list_polls(conn):
    """Return all polls in creation order with their option count and total votes."""
    rows = conn.execute(
        """
        SELECT p.id, p.title, p.description,
               (SELECT COUNT(*) FROM options o WHERE o.poll_id = p.id) AS option_count,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total_votes
        FROM polls p
        ORDER BY p.id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_poll(conn, poll_id):
    """Return one poll with its options in display order, or None when the poll does not exist."""
    poll = conn.execute(
        "SELECT id, title, description FROM polls WHERE id = ?", (poll_id,)
    ).fetchone()
    if poll is None:
        return None
    options = conn.execute(
        "SELECT id, text, position FROM options WHERE poll_id = ? ORDER BY position",
        (poll_id,),
    ).fetchall()
    result = dict(poll)
    result["options"] = [dict(row) for row in options]
    return result


def has_voted(conn, poll_id, voter_token):
    """Return True when the voter token already has a vote in the poll. A missing token has not voted."""
    if not voter_token:
        return False
    row = conn.execute(
        "SELECT 1 FROM votes WHERE poll_id = ? AND voter_token = ?",
        (poll_id, voter_token),
    ).fetchone()
    return row is not None


def cast_vote(conn, poll_id, option_id, voter_token):
    """Record one vote for option_id in poll_id.

    option_id is the raw form value. It must be an integer naming an option of this poll.
    The insert relies on the UNIQUE(poll_id, voter_token) constraint, so a second vote from the
    same token is refused even when two requests race. Raises VoteError on refusal; nothing is stored then.
    """
    if option_id is None or str(option_id).strip() == "":
        raise VoteError(NOT_SELECTED)
    try:
        option_key = int(str(option_id).strip())
    except ValueError:
        raise VoteError(INVALID_OPTION)

    valid = conn.execute(
        "SELECT 1 FROM options WHERE id = ? AND poll_id = ?", (option_key, poll_id)
    ).fetchone()
    if valid is None:
        raise VoteError(INVALID_OPTION)

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO votes (poll_id, option_id, voter_token, created_at) VALUES (?, ?, ?, ?)",
            (poll_id, option_key, voter_token, created_at),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise VoteError(ALREADY_VOTED)


def get_results(conn, poll_id):
    """Return the title, total votes and per-option counts and percentages for a poll.

    Returns None when the poll does not exist. Options are listed in display order.
    """
    poll = conn.execute(
        "SELECT id, title FROM polls WHERE id = ?", (poll_id,)
    ).fetchone()
    if poll is None:
        return None
    rows = conn.execute(
        """
        SELECT o.id AS option_id, o.text, COUNT(v.id) AS votes
        FROM options o
        LEFT JOIN votes v ON v.option_id = o.id
        WHERE o.poll_id = ?
        GROUP BY o.id, o.text, o.position
        ORDER BY o.position
        """,
        (poll_id,),
    ).fetchall()
    total = sum(row["votes"] for row in rows)
    results = [
        {
            "option_id": row["option_id"],
            "text": row["text"],
            "votes": row["votes"],
            "percent": _percent(row["votes"], total),
        }
        for row in rows
    ]
    return {"id": poll["id"], "title": poll["title"], "total_votes": total, "results": results}


def list_poll_summaries(conn):
    """Return every poll with its total vote count, in creation order."""
    rows = conn.execute(
        """
        SELECT p.id, p.title,
               (SELECT COUNT(*) FROM votes v WHERE v.poll_id = p.id) AS total_votes
        FROM polls p
        ORDER BY p.id
        """
    ).fetchall()
    return [dict(row) for row in rows]

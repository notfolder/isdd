"""Business rules for casting votes and computing results."""

import sqlite3
from typing import Any, Optional

from .repository import PollRepository


class PollNotFound(Exception):
    """Raised when the poll does not exist."""


class InvalidPoll(Exception):
    """Raised when a new poll's question or options break the input rules. Nothing is recorded."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidVote(Exception):
    """Raised when the submitted option is missing or does not belong to the poll."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


QUESTION_MAX_LENGTH = 200
OPTION_MAX_LENGTH = 100
MIN_OPTIONS = 2


class VotingService:
    """Casts votes (one vote per voter per poll), creates polls and builds result summaries."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.repo = PollRepository(conn)

    def cast_vote(self, poll_id: int, option_id: Optional[int], voter_id: str, voted_at: str) -> str:
        """Record a vote in one transaction. Return "recorded" or "already_voted".

        Raises PollNotFound when the poll does not exist and InvalidVote when no option was chosen
        or the option belongs to another poll. Nothing is recorded in those cases.
        """
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            if self.repo.get_poll(poll_id) is None:
                raise PollNotFound(poll_id)
            if option_id is None:
                raise InvalidVote("Please choose an option.")
            option = self.repo.get_option(option_id)
            if option is None or option["poll_id"] != poll_id:
                raise InvalidVote("That option is not part of this poll.")
            if self.repo.find_vote(poll_id, voter_id) is not None:
                self.conn.execute("COMMIT")
                return "already_voted"
            inserted = self.repo.insert_vote(poll_id, option_id, voter_id, voted_at)
            self.conn.execute("COMMIT")
            return "recorded" if inserted else "already_voted"
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def create_poll(self, question: str, options: list[str], created_at: str) -> int:
        """Create a poll with its options in one transaction and return the poll id.

        The question and each option are stripped; empty options are ignored. Raises InvalidPoll (and records
        nothing) when the question is empty or longer than 200 characters, when fewer than 2 options remain,
        when an option is longer than 100 characters, or when two options have the same text.
        Options are stored in the order given, with positions starting at 1.
        """
        question = question.strip()
        kept = [o.strip() for o in options if o.strip()]
        if not question:
            raise InvalidPoll("Please enter a question.")
        if len(question) > QUESTION_MAX_LENGTH:
            raise InvalidPoll("The question must be 200 characters or fewer.")
        if len(kept) < MIN_OPTIONS:
            raise InvalidPoll("Please enter at least two options.")
        if any(len(o) > OPTION_MAX_LENGTH for o in kept):
            raise InvalidPoll("Each option must be 100 characters or fewer.")
        if len(set(kept)) != len(kept):
            raise InvalidPoll("Each option must be different.")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            poll_id = self.repo.insert_poll(question, "", created_at)
            for position, label in enumerate(kept, start=1):
                self.repo.insert_option(poll_id, label, position)
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return poll_id

    def get_poll_result(self, poll_id: int) -> Optional[dict[str, Any]]:
        """Return the question, each option's votes and percentage, and the total; None if no such poll."""
        poll = self.repo.get_poll(poll_id)
        if poll is None:
            return None
        counts = self.repo.count_votes_by_option(poll_id)
        options = []
        for option in self.repo.list_options(poll_id):
            options.append({"id": option["id"], "label": option["label"], "votes": counts.get(option["id"], 0)})
        total = sum(o["votes"] for o in options)
        for o in options:
            o["percent"] = round(o["votes"] * 100 / total) if total else 0
        return {"id": poll["id"], "question": poll["question"], "options": options, "total": total}

    def get_all_results(self) -> list[dict[str, Any]]:
        """Return the result summary of every poll in id order."""
        results = []
        for poll in self.repo.list_polls():
            result = self.get_poll_result(poll["id"])
            if result is not None:
                results.append(result)
        return results

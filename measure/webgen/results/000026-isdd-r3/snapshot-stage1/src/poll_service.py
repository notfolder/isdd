"""Business logic for polls: listing, voting and result totals."""

import storage


class PollNotFoundError(Exception):
    """Raised when the requested poll does not exist."""


class NoOptionSelectedError(Exception):
    """Raised when no option was selected, or the option does not belong to the poll."""


class PollService:
    """Lists polls, records votes and calculates results on one database connection."""

    def __init__(self, conn):
        """Keep the sqlite3 connection used for every operation."""
        self._conn = conn

    def list_polls(self):
        """Return every poll with its option count and total votes."""
        return storage.list_polls_with_totals(self._conn)

    def get_poll(self, poll_id):
        """Return {"poll": {...}, "options": [...]} for the poll.

        Raises PollNotFoundError when the poll does not exist.
        """
        poll = storage.find_poll(self._conn, poll_id)
        if poll is None:
            raise PollNotFoundError(poll_id)
        options = storage.list_options_with_counts(self._conn, poll_id)
        return {"poll": poll, "options": options}

    def cast_vote(self, poll_id, option_id):
        """Record one vote for option_id in poll_id and return the chosen option.

        Raises PollNotFoundError when the poll does not exist.
        Raises NoOptionSelectedError when option_id is None or does not belong to the poll.
        """
        if storage.find_poll(self._conn, poll_id) is None:
            raise PollNotFoundError(poll_id)
        if option_id is None:
            raise NoOptionSelectedError(poll_id)
        option = storage.find_option(self._conn, poll_id, option_id)
        if option is None:
            raise NoOptionSelectedError(poll_id)
        storage.insert_vote(self._conn, option_id)
        return option

    def get_poll_results(self, poll_id):
        """Return {"poll", "total", "options"} where each option has votes and percent.

        Percent is rounded to one decimal place; it is 0.0 when there are no votes.
        Raises PollNotFoundError when the poll does not exist.
        """
        detail = self.get_poll(poll_id)
        options = []
        total = 0
        for option in detail["options"]:
            total += option["votes"]
        for option in detail["options"]:
            percent = round(option["votes"] * 100 / total, 1) if total else 0.0
            options.append(
                {"id": option["id"], "text": option["text"],
                 "votes": option["votes"], "percent": percent}
            )
        return {"poll": detail["poll"], "total": total, "options": options}

    def get_all_results(self):
        """Return the results of every poll, in poll id order."""
        return [self.get_poll_results(poll["id"]) for poll in self.list_polls()]

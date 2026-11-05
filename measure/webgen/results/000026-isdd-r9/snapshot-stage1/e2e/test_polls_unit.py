"""Unit tests for PollService using a temporary SQLite database."""

import secrets
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from db import Database  # noqa: E402
from polls import (  # noqa: E402
    VOTE_ALREADY_VOTED,
    VOTE_INVALID_OPTION,
    VOTE_NO_OPTION,
    VOTE_NOT_FOUND,
    VOTE_OK,
    PollService,
)
from seed import SampleSeeder  # noqa: E402


class PollServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self._tmp.name) / "polls.db")
        self.db.ensure_schema()
        SampleSeeder(self.db).seed_if_empty()
        self.service = PollService(self.db)
        # Sample poll 1 ("Favorite season?") has options 1..4; sample poll 2 has no votes.
        self.poll1_options = [o["id"] for o in self.service.get_poll(1)["options"]]

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_vote_is_recorded_once_per_voter(self) -> None:
        voter = secrets.token_hex(16)
        self.assertEqual(self.service.cast_vote(1, self.poll1_options[0], voter), VOTE_OK)
        self.assertEqual(self.service.cast_vote(1, self.poll1_options[1], voter), VOTE_ALREADY_VOTED)

    def test_missing_option_is_rejected_and_not_stored(self) -> None:
        before = self.service.get_results(1)["total_votes"]
        self.assertEqual(self.service.cast_vote(1, None, secrets.token_hex(16)), VOTE_NO_OPTION)
        self.assertEqual(self.service.get_results(1)["total_votes"], before)

    def test_option_from_another_poll_is_invalid(self) -> None:
        other_option = self.service.get_poll(2)["options"][0]["id"]
        self.assertEqual(self.service.cast_vote(1, other_option, secrets.token_hex(16)), VOTE_INVALID_OPTION)

    def test_unknown_poll_is_not_found(self) -> None:
        self.assertEqual(self.service.cast_vote(99999, 1, secrets.token_hex(16)), VOTE_NOT_FOUND)

    def test_results_percent_and_total(self) -> None:
        data = self.service.get_results(1)
        self.assertEqual(data["total_votes"], 11)
        summer = next(o for o in data["options"] if o["label"] == "Summer")
        self.assertEqual(summer["votes"], 5)
        self.assertEqual(summer["percent"], round(5 * 100 / 11, 1))

    def test_results_without_votes_are_zero_percent(self) -> None:
        data = self.service.get_results(2)
        self.assertEqual(data["total_votes"], 0)
        self.assertTrue(all(o["percent"] == 0.0 for o in data["options"]))

    def test_seeding_does_nothing_when_polls_exist(self) -> None:
        self.assertFalse(SampleSeeder(self.db).seed_if_empty())
        self.assertEqual(len(self.service.list_polls()), 3)


if __name__ == "__main__":
    unittest.main()

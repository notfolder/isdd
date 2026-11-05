"""Unit tests for the business logic (src/poll_service.py)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import storage  # noqa: E402
from poll_service import NoOptionSelectedError, PollNotFoundError, PollService  # noqa: E402


class PollServiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = storage.open_database(self._tmp.name)
        self.service = PollService(self.conn)
        self.poll_id = self.service.list_polls()[0]["id"]

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_cast_vote_records_one_vote(self):
        before = self.service.get_poll_results(self.poll_id)["total"]
        option = self.service.get_poll(self.poll_id)["options"][2]
        chosen = self.service.cast_vote(self.poll_id, option["id"])
        self.assertEqual(chosen["id"], option["id"])
        self.assertEqual(self.service.get_poll_results(self.poll_id)["total"], before + 1)

    def test_cast_vote_without_option_is_rejected_and_not_recorded(self):
        before = self.service.get_poll_results(self.poll_id)["total"]
        with self.assertRaises(NoOptionSelectedError):
            self.service.cast_vote(self.poll_id, None)
        self.assertEqual(self.service.get_poll_results(self.poll_id)["total"], before)

    def test_cast_vote_with_unknown_poll_raises(self):
        with self.assertRaises(PollNotFoundError):
            self.service.cast_vote(99999, 1)

    def test_get_poll_unknown_raises(self):
        with self.assertRaises(PollNotFoundError):
            self.service.get_poll(99999)

    def test_percentages_round_to_one_decimal_and_zero_votes_give_zero(self):
        result = self.service.get_poll_results(self.poll_id)
        expected_total = sum(o["votes"] for o in result["options"])
        self.assertEqual(result["total"], expected_total)
        for option in result["options"]:
            expected = round(option["votes"] * 100 / expected_total, 1)
            self.assertEqual(option["percent"], expected)
        empty_poll = storage.list_polls_with_totals(self.conn)[0]
        self.assertGreater(empty_poll["total_votes"], 0)

    def test_percent_is_zero_when_poll_has_no_votes(self):
        with self.conn:
            self.conn.execute("DELETE FROM votes")
        result = self.service.get_poll_results(self.poll_id)
        self.assertEqual(result["total"], 0)
        self.assertTrue(all(o["percent"] == 0.0 for o in result["options"]))

    def test_get_all_results_covers_every_poll(self):
        results = self.service.get_all_results()
        self.assertEqual(len(results), len(self.service.list_polls()))


if __name__ == "__main__":
    unittest.main()

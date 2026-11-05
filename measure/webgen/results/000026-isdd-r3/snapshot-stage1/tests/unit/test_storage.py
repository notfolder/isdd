"""Unit tests for the storage layer (src/storage.py)."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import storage  # noqa: E402


class StorageTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = storage.open_database(Path(self._tmp.name) / "data")

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_open_database_creates_file_and_seeds_sample_polls(self):
        self.assertTrue((Path(self._tmp.name) / "data" / storage.DB_FILE_NAME).exists())
        polls = storage.list_polls_with_totals(self.conn)
        self.assertEqual(len(polls), len(storage.SAMPLE_POLLS))
        self.assertGreater(polls[0]["total_votes"], 0)

    def test_seed_does_not_run_again_when_polls_exist(self):
        before = storage.list_polls_with_totals(self.conn)
        storage.seed_sample_data(self.conn)
        self.assertEqual(storage.list_polls_with_totals(self.conn), before)

    def test_insert_vote_increases_count_for_option_only(self):
        poll = storage.list_polls_with_totals(self.conn)[0]
        options = storage.list_options_with_counts(self.conn, poll["id"])
        target = options[0]
        storage.insert_vote(self.conn, target["id"])
        after = {o["id"]: o["votes"] for o in storage.list_options_with_counts(self.conn, poll["id"])}
        self.assertEqual(after[target["id"]], target["votes"] + 1)
        for other in options[1:]:
            self.assertEqual(after[other["id"]], other["votes"])

    def test_find_option_rejects_option_from_other_poll(self):
        polls = storage.list_polls_with_totals(self.conn)
        option_of_second = storage.list_options_with_counts(self.conn, polls[1]["id"])[0]
        self.assertIsNone(storage.find_option(self.conn, polls[0]["id"], option_of_second["id"]))

    def test_find_poll_returns_none_for_missing_id(self):
        self.assertIsNone(storage.find_poll(self.conn, 99999))

    def test_foreign_key_blocks_vote_for_missing_option(self):
        with self.assertRaises(sqlite3.IntegrityError):
            storage.insert_vote(self.conn, 99999)


if __name__ == "__main__":
    unittest.main()

"""保存処理の単体テスト（標準ライブラリの unittest。一時ディレクトリの SQLite を使う）。"""

import os
import sqlite3
import tempfile
import unittest

from store.db import cast_vote, get_poll, init_db, list_polls, seed_sample_polls


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "polls.db")
        init_db(self.db)
        seed_sample_polls(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_seed_fills_three_polls_once(self):
        self.assertEqual(len(list_polls(self.db)), 3)
        seed_sample_polls(self.db)
        self.assertEqual(len(list_polls(self.db)), 3)

    def test_list_polls_reports_totals_and_leader(self):
        polls = list_polls(self.db)
        first = polls[0]
        self.assertEqual(first["total"], 10)
        self.assertEqual(first["option_count"], 4)
        self.assertEqual(first["leader"], "Python")

    def test_get_poll_returns_counts_and_percentages(self):
        poll = get_poll(self.db, 2)
        self.assertEqual(poll["total"], 11)
        summer = [o for o in poll["options"] if o["text"] == "Summer"][0]
        self.assertEqual(summer["votes"], 5)
        self.assertEqual(summer["percent"], round(5 * 100 / 11, 1))

    def test_get_poll_missing_returns_none(self):
        self.assertIsNone(get_poll(self.db, 9999))

    def test_cast_vote_counts_every_submission(self):
        poll = get_poll(self.db, 1)
        python = [o for o in poll["options"] if o["text"] == "Python"][0]
        cast_vote(self.db, 1, python["id"])
        cast_vote(self.db, 1, python["id"])
        after = get_poll(self.db, 1)
        python_after = [o for o in after["options"] if o["text"] == "Python"][0]
        self.assertEqual(python_after["votes"], python["votes"] + 2)
        self.assertEqual(after["total"], poll["total"] + 2)

    def test_cast_vote_rejects_option_of_other_poll(self):
        other = get_poll(self.db, 2)["options"][0]["id"]
        before = get_poll(self.db, 1)["total"]
        with self.assertRaises(ValueError):
            cast_vote(self.db, 1, other)
        self.assertEqual(get_poll(self.db, 1)["total"], before)

    def test_cast_vote_rejects_unknown_option(self):
        before = get_poll(self.db, 1)["total"]
        with self.assertRaises(ValueError):
            cast_vote(self.db, 1, 999999)
        self.assertEqual(get_poll(self.db, 1)["total"], before)

    def test_poll_with_no_votes_shows_zero_percent(self):
        conn = sqlite3.connect(self.db)
        with conn:
            poll_id = conn.execute(
                "INSERT INTO polls (question, description) VALUES ('Empty?', NULL)"
            ).lastrowid
            conn.execute(
                "INSERT INTO poll_options (poll_id, text) VALUES (?, 'Only')", (poll_id,)
            )
        conn.close()
        poll = get_poll(self.db, poll_id)
        self.assertEqual(poll["total"], 0)
        self.assertEqual(poll["options"][0]["percent"], 0.0)
        empty = [p for p in list_polls(self.db) if p["id"] == poll_id][0]
        self.assertIsNone(empty["leader"])


if __name__ == "__main__":
    unittest.main()

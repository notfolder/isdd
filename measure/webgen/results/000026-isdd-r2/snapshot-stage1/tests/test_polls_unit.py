"""Unit and integration tests for the database, poll logic, voter cookie and sample data."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db  # noqa: E402
import polls  # noqa: E402
import sample_data  # noqa: E402
import voter  # noqa: E402


class DatabaseTestCase(unittest.TestCase):
    """Creates a fresh temporary database for each test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.conn = db.get_db(self._tmp.name)
        db.init_db(self.conn)

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def add_poll(self, title="Question", options=("A", "B")):
        cursor = self.conn.execute("INSERT INTO polls (title, description) VALUES (?, ?)", (title, "desc"))
        poll_id = cursor.lastrowid
        option_ids = []
        for position, text in enumerate(options):
            option_cursor = self.conn.execute(
                "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)", (poll_id, text, position)
            )
            option_ids.append(option_cursor.lastrowid)
        self.conn.commit()
        return poll_id, option_ids


class DatabaseSchemaTest(DatabaseTestCase):
    def test_init_db_creates_tables_and_is_repeatable(self):
        db.init_db(self.conn)
        tables = {
            row[0] for row in self.conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        self.assertTrue({"polls", "options", "votes"} <= tables)

    def test_get_db_creates_missing_directory(self):
        nested = Path(self._tmp.name) / "a" / "b"
        conn = db.get_db(nested)
        try:
            self.assertTrue((nested / "polls.db").exists())
        finally:
            conn.close()

    def test_one_vote_per_token_per_poll_is_enforced_by_database(self):
        poll_id, option_ids = self.add_poll()
        self.conn.execute(
            "INSERT INTO votes (poll_id, option_id, voter_token, created_at) VALUES (?, ?, ?, ?)",
            (poll_id, option_ids[0], "t" * 32, "2026-01-01 00:00:00"),
        )
        with self.assertRaises(Exception):
            self.conn.execute(
                "INSERT INTO votes (poll_id, option_id, voter_token, created_at) VALUES (?, ?, ?, ?)",
                (poll_id, option_ids[1], "t" * 32, "2026-01-01 00:00:00"),
            )


class PollLogicTest(DatabaseTestCase):
    def test_list_polls_counts_options_and_votes(self):
        poll_id, option_ids = self.add_poll(options=("A", "B", "C"))
        polls.cast_vote(self.conn, poll_id, str(option_ids[0]), "x" * 32)
        rows = polls.list_polls(self.conn)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["option_count"], 3)
        self.assertEqual(rows[0]["total_votes"], 1)

    def test_get_poll_returns_options_in_position_order(self):
        poll_id, _ = self.add_poll(options=("first", "second"))
        poll = polls.get_poll(self.conn, poll_id)
        self.assertEqual([o["text"] for o in poll["options"]], ["first", "second"])

    def test_get_poll_returns_none_for_missing_poll(self):
        self.assertIsNone(polls.get_poll(self.conn, 999))

    def test_cast_vote_records_vote_and_has_voted_reports_it(self):
        poll_id, option_ids = self.add_poll()
        token = voter.issue_voter_token()
        self.assertFalse(polls.has_voted(self.conn, poll_id, token))
        polls.cast_vote(self.conn, poll_id, str(option_ids[1]), token)
        self.assertTrue(polls.has_voted(self.conn, poll_id, token))

    def test_cast_vote_rejects_second_vote_in_same_poll(self):
        poll_id, option_ids = self.add_poll()
        polls.cast_vote(self.conn, poll_id, str(option_ids[0]), "y" * 32)
        with self.assertRaises(polls.VoteError) as ctx:
            polls.cast_vote(self.conn, poll_id, str(option_ids[1]), "y" * 32)
        self.assertEqual(ctx.exception.code, polls.ALREADY_VOTED)
        results = polls.get_results(self.conn, poll_id)
        self.assertEqual(results["total_votes"], 1)

    def test_cast_vote_allows_same_token_in_another_poll(self):
        first, first_options = self.add_poll("one")
        second, second_options = self.add_poll("two")
        polls.cast_vote(self.conn, first, str(first_options[0]), "z" * 32)
        polls.cast_vote(self.conn, second, str(second_options[0]), "z" * 32)
        self.assertEqual(polls.get_results(self.conn, second)["total_votes"], 1)

    def test_cast_vote_without_selection_is_refused(self):
        poll_id, _ = self.add_poll()
        for empty in (None, "", "   "):
            with self.subTest(value=empty):
                with self.assertRaises(polls.VoteError) as ctx:
                    polls.cast_vote(self.conn, poll_id, empty, "q" * 32)
                self.assertEqual(ctx.exception.code, polls.NOT_SELECTED)

    def test_cast_vote_rejects_non_numeric_and_foreign_options(self):
        poll_id, _ = self.add_poll("first")
        _, other_options = self.add_poll("second")
        for bad in ("abc", str(other_options[0]), "9999"):
            with self.subTest(value=bad):
                with self.assertRaises(polls.VoteError) as ctx:
                    polls.cast_vote(self.conn, poll_id, bad, "r" * 32)
                self.assertEqual(ctx.exception.code, polls.INVALID_OPTION)
        self.assertEqual(polls.get_results(self.conn, poll_id)["total_votes"], 0)

    def test_results_compute_counts_and_one_decimal_percentages(self):
        poll_id, option_ids = self.add_poll(options=("A", "B", "C"))
        votes = [(option_ids[0], "a" * 32), (option_ids[0], "b" * 32), (option_ids[1], "c" * 32)]
        for option_id, token in votes:
            polls.cast_vote(self.conn, poll_id, str(option_id), token)
        result = polls.get_results(self.conn, poll_id)
        self.assertEqual(result["total_votes"], 3)
        counts = {row["text"]: (row["votes"], row["percent"]) for row in result["results"]}
        self.assertEqual(counts["A"], (2, 66.7))
        self.assertEqual(counts["B"], (1, 33.3))
        self.assertEqual(counts["C"], (0, 0.0))

    def test_results_with_no_votes_show_zero_percent(self):
        poll_id, _ = self.add_poll()
        result = polls.get_results(self.conn, poll_id)
        self.assertEqual(result["total_votes"], 0)
        self.assertTrue(all(row["percent"] == 0.0 for row in result["results"]))

    def test_get_results_returns_none_for_missing_poll(self):
        self.assertIsNone(polls.get_results(self.conn, 404))

    def test_list_poll_summaries_reports_total_votes(self):
        poll_id, option_ids = self.add_poll()
        polls.cast_vote(self.conn, poll_id, str(option_ids[0]), "s" * 32)
        summaries = polls.list_poll_summaries(self.conn)
        self.assertEqual(summaries[0]["total_votes"], 1)


class VoterTokenTest(unittest.TestCase):
    def test_issued_token_is_32_letters_and_digits(self):
        token = voter.issue_voter_token()
        self.assertEqual(len(token), voter.TOKEN_LENGTH)
        self.assertTrue(all(ch.isascii() and ch.isalnum() for ch in token))

    def test_issued_tokens_differ(self):
        self.assertNotEqual(voter.issue_voter_token(), voter.issue_voter_token())

    def test_get_voter_token_reads_valid_cookie_only(self):
        token = voter.issue_voter_token()
        self.assertEqual(voter.get_voter_token({voter.COOKIE_NAME: token}), token)
        self.assertIsNone(voter.get_voter_token({}))
        self.assertIsNone(voter.get_voter_token({voter.COOKIE_NAME: "short"}))
        self.assertIsNone(voter.get_voter_token({voter.COOKIE_NAME: "<script>" + "a" * 24}))


class SampleDataTest(DatabaseTestCase):
    def test_seed_inserts_three_polls_only_when_empty(self):
        self.assertTrue(sample_data.seed_sample_data(self.conn))
        self.assertEqual(len(polls.list_polls(self.conn)), 3)
        self.assertFalse(sample_data.seed_sample_data(self.conn))
        self.assertEqual(len(polls.list_polls(self.conn)), 3)

    def test_sample_polls_have_options_and_votes(self):
        sample_data.seed_sample_data(self.conn)
        for poll in polls.list_polls(self.conn):
            self.assertGreaterEqual(poll["option_count"], 3)
            self.assertGreater(poll["total_votes"], 0)


if __name__ == "__main__":
    unittest.main()

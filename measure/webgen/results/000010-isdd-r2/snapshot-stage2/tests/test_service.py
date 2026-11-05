"""業務ロジックの単体テスト: 名前の検証、抽選、景品 0 件、範囲外のパス。"""

import os
import random
import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.server import _is_inside
from app.service import NAME_MAX_LENGTH, RequestError, SpinService, validate_player_name


class ValidatePlayerNameTest(unittest.TestCase):
    def test_trims_surrounding_spaces(self) -> None:
        self.assertEqual(validate_player_name("  Alice  "), "Alice")

    def test_empty_name_is_rejected(self) -> None:
        for raw in ["", "   ", None, 12]:
            with self.subTest(raw=raw):
                with self.assertRaises(RequestError) as caught:
                    validate_player_name(raw)
                self.assertEqual(caught.exception.status, 400)
                self.assertEqual(caught.exception.message, "Please enter your name.")

    def test_thirty_characters_is_accepted(self) -> None:
        name = "a" * NAME_MAX_LENGTH
        self.assertEqual(validate_player_name(name), name)

    def test_thirty_one_characters_is_rejected(self) -> None:
        with self.assertRaises(RequestError) as caught:
            validate_player_name("a" * (NAME_MAX_LENGTH + 1))
        self.assertEqual(caught.exception.message, "Name must be 30 characters or fewer.")


class SpinServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self._tmp.name, "wheel.sqlite3"))
        self.db.initialize()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_spin_returns_prize_within_range_and_records_it(self) -> None:
        service = SpinService(self.db, random.Random(1))
        result = service.spin("Dana")
        self.assertEqual(result["prize_count"], len(self.db.list_prizes()))
        self.assertTrue(0 <= result["prize_index"] < result["prize_count"])
        self.assertEqual(result["prize"]["id"], result["record"]["prize_id"])
        self.assertEqual(result["record"]["player_name"], "Dana")
        self.assertEqual(len(service.get_winnings("Dana")["winnings"]), 1)

    def test_spin_with_fixed_seed_picks_the_same_index(self) -> None:
        first = SpinService(self.db, random.Random(7)).spin("Eve")["prize_index"]
        second = SpinService(self.db, random.Random(7)).spin("Eve")["prize_index"]
        self.assertEqual(first, second)

    def test_spin_without_prizes_is_refused_and_records_nothing(self) -> None:
        empty = Database(os.path.join(self._tmp.name, "empty.sqlite3"))
        empty.initialize()
        conn = empty._connect()
        with conn:
            conn.execute("DELETE FROM winning_records")
            conn.execute("DELETE FROM prizes")
        conn.close()
        service = SpinService(empty, random.Random(3))
        with self.assertRaises(RequestError) as caught:
            service.spin("Frank")
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(caught.exception.message, "No prizes are available right now.")
        self.assertEqual(service.get_winnings("Frank")["winnings"], [])

    def test_invalid_name_is_refused_and_records_nothing(self) -> None:
        service = SpinService(self.db, random.Random(3))
        before = len(self.db.list_winnings_by_name("Sample Player"))
        with self.assertRaises(RequestError):
            service.spin("   ")
        self.assertEqual(len(self.db.list_winnings_by_name("Sample Player")), before)

    def test_every_prize_can_be_drawn(self) -> None:
        service = SpinService(self.db, random.Random(11))
        seen = {service.spin("Odds")["prize"]["id"] for _ in range(300)}
        self.assertEqual(seen, {prize["id"] for prize in self.db.list_prizes()})


class PathContainmentTest(unittest.TestCase):
    """静的ファイルの範囲確認。要求のパスは解決してから比べる（serve_static と同じ手順）。"""

    def setUp(self) -> None:
        self.root = Path(tempfile.gettempdir()).resolve() / "wheel-root-check"

    def test_paths_inside_root_are_accepted(self) -> None:
        self.assertTrue(_is_inside((self.root / "a.css").resolve(), self.root))

    def test_paths_outside_root_are_refused(self) -> None:
        self.assertFalse(_is_inside((self.root / ".." / "secret.txt").resolve(), self.root))


if __name__ == "__main__":
    unittest.main()

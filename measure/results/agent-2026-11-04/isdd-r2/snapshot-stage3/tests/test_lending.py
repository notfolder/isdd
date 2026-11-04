"""貸出と返却、版番号による修正の拒否、同時の貸出・返却の単体・結合テスト（一時 DB）。"""

import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from equipment_ledger.core import validation  # noqa: E402
from equipment_ledger.core.accounts import ROLE_MEMBER, list_borrower_candidates, register_account  # noqa: E402
from equipment_ledger.core.db import initialize_schema, open_connection  # noqa: E402
from equipment_ledger.core.equipment import (  # noqa: E402
    DELETE_LENT,
    DELETE_MISSING,
    DELETE_OK,
    delete_equipment,
    get_equipment,
    list_equipment_status,
    register_equipment,
    update_equipment,
)
from equipment_ledger.core.lending import (  # noqa: E402
    LEND_ALREADY_LENT,
    LEND_NO_BORROWER,
    LEND_NO_EQUIPMENT,
    LEND_OK,
    RETURN_ALREADY,
    RETURN_NO_EQUIPMENT,
    RETURN_OK,
    lend_equipment,
    return_equipment,
)


class _DbCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = open_connection(self.tmp.name)
        initialize_schema(self.conn)
        register_account(self.conn, "111111", "担当", "12345678")
        register_account(self.conn, "222222", "社員", "12345678")
        register_equipment(self.conn, "PC-0001", "ノートパソコン")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()


class LendingTest(_DbCase):
    def test_lend_then_already_lent(self):
        self.assertEqual(lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04"), LEND_OK)
        self.assertEqual(lend_equipment(self.conn, "PC-0001", "111111", "2026-11-04"), LEND_ALREADY_LENT)

    def test_lend_missing_equipment_or_borrower(self):
        self.assertEqual(lend_equipment(self.conn, "NONE", "222222", "2026-11-04"), LEND_NO_EQUIPMENT)
        self.assertEqual(lend_equipment(self.conn, "PC-0001", "999999", "2026-11-04"), LEND_NO_BORROWER)

    def test_status_shows_holder_and_date(self):
        lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04")
        row = list_equipment_status(self.conn)[0]
        self.assertEqual((row["status"], row["holder_name"], row["lent_on"]), ("貸出中", "社員", "2026-11-04"))

    def test_return_removes_record_and_second_return_is_rejected(self):
        lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04")
        self.assertEqual(return_equipment(self.conn, "PC-0001"), RETURN_OK)
        self.assertEqual(return_equipment(self.conn, "PC-0001"), RETURN_ALREADY)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM lending").fetchone()[0], 0)
        self.assertEqual(return_equipment(self.conn, "NONE"), RETURN_NO_EQUIPMENT)

    def test_delete_refused_while_lent(self):
        lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04")
        self.assertEqual(delete_equipment(self.conn, "PC-0001"), DELETE_LENT)
        self.assertIsNotNone(get_equipment(self.conn, "PC-0001"))
        return_equipment(self.conn, "PC-0001")
        self.assertEqual(delete_equipment(self.conn, "PC-0001"), DELETE_OK)
        self.assertEqual(delete_equipment(self.conn, "PC-0001"), DELETE_MISSING)

    def test_update_keeps_lending_and_rejects_stale_revision(self):
        lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04")
        first = get_equipment(self.conn, "PC-0001")["revision"]
        self.assertTrue(update_equipment(self.conn, "PC-0001", "新しい名前", first))
        self.assertFalse(update_equipment(self.conn, "PC-0001", "古い開き方", first))
        row = list_equipment_status(self.conn)[0]
        self.assertEqual((row["name"], row["status"], row["holder_name"]), ("新しい名前", "貸出中", "社員"))

    def test_stale_revision_after_delete_is_rejected(self):
        revision = get_equipment(self.conn, "PC-0001")["revision"]
        delete_equipment(self.conn, "PC-0001")
        self.assertFalse(update_equipment(self.conn, "PC-0001", "x", revision))

    def test_borrower_candidates_are_all_accounts(self):
        names = [c["employee_number"] for c in list_borrower_candidates(self.conn)]
        self.assertEqual(names, ["111111", "222222"])


class ConcurrencyTest(_DbCase):
    def _race(self, action):
        """2 つの接続から同時に action を実行し、結果の一覧を返す。"""
        barrier = threading.Barrier(2)
        results = []
        lock = threading.Lock()

        def worker():
            conn = open_connection(self.tmp.name)
            try:
                barrier.wait()
                result = action(conn)
            finally:
                conn.close()
            with lock:
                results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return sorted(results)

    def test_concurrent_lend_only_first_is_recorded(self):
        results = self._race(lambda c: lend_equipment(c, "PC-0001", "222222", "2026-11-04"))
        self.assertEqual(results, sorted([LEND_OK, LEND_ALREADY_LENT]))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM lending").fetchone()[0], 1)

    def test_concurrent_return_only_first_is_processed(self):
        lend_equipment(self.conn, "PC-0001", "222222", "2026-11-04")
        results = self._race(lambda c: return_equipment(c, "PC-0001"))
        self.assertEqual(results, sorted([RETURN_OK, RETURN_ALREADY]))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM lending").fetchone()[0], 0)


class MigrationTest(unittest.TestCase):
    def test_old_equipment_table_gets_revision_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = sqlite3.connect(os.path.join(tmp, "equipment_ledger.db"))
            raw.execute("CREATE TABLE equipment (equipment_number TEXT PRIMARY KEY NOT NULL, name TEXT NOT NULL)")
            raw.execute("INSERT INTO equipment VALUES ('PC-0001', '旧')")
            raw.commit()
            raw.close()
            conn = open_connection(tmp)
            initialize_schema(conn)
            initialize_schema(conn)
            self.assertEqual(get_equipment(conn, "PC-0001"), {"number": "PC-0001", "name": "旧", "revision": 0})
            conn.close()


class LendingValidationTest(unittest.TestCase):
    today = date(2026, 11, 4)

    def test_borrower_required(self):
        errors = validation.validate_lending_input("", "2026-11-04", self.today)
        self.assertEqual(errors["borrower"], "借りる社員を選んでください")

    def test_date_bounds(self):
        self.assertEqual(validation.validate_lending_input("222222", "2026-11-04", self.today), {})
        self.assertEqual(validation.validate_lending_input("222222", "2026-11-03", self.today), {})
        errors = validation.validate_lending_input("222222", "2026-11-05", self.today)
        self.assertEqual(errors["lent_on"], "貸出日に未来の日付は入力できません")

    def test_date_format(self):
        for bad in ["2026-2-3", "2026/11/04", "2026-02-30", ""]:
            errors = validation.validate_lending_input("222222", bad, self.today)
            self.assertEqual(errors["lent_on"], "貸出日は YYYY-MM-DD の形式で入力してください", bad)


if __name__ == "__main__":
    unittest.main()

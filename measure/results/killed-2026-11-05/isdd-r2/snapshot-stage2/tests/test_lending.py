"""貸出・返却の単体テスト。同時の場面は、同じ一時 DB に別々の接続で続けて操作して確かめる。"""

import threading
import unittest
from datetime import datetime, timedelta, timezone

from src import accounts, db, equipment, lending
from tests.helpers import make_data_dir


class LendingTest(unittest.TestCase):
    def setUp(self):
        self.data_dir = make_data_dir()
        self.conn = db.connect(self.data_dir)
        accounts.register_account(self.conn, "0000001", "担当", "password1")
        accounts.register_account(self.conn, "0000002", "社員", "password2")
        equipment.create_equipment(self.conn, "A-1", "ノート")

    def tearDown(self):
        self.conn.close()

    def test_lend_then_second_lend_is_already_lent(self):
        self.assertEqual(
            lending.lend_equipment(self.conn, "A-1", "0000002", "2026-11-05"), ({}, lending.STATUS_OK)
        )
        self.assertEqual(
            lending.lend_equipment(self.conn, "A-1", "0000001", "2026-11-05"),
            ({}, lending.STATUS_ALREADY_LENT),
        )
        row = self.conn.execute("SELECT employee_number FROM lendings").fetchone()
        self.assertEqual(row["employee_number"], "0000002")

    def test_lend_missing_equipment_is_not_found(self):
        _, status = lending.lend_equipment(self.conn, "NONE", "0000002", "2026-11-05")
        self.assertEqual(status, lending.STATUS_NOT_FOUND)

    def test_lend_to_unknown_employee_is_invalid(self):
        errors, status = lending.lend_equipment(self.conn, "A-1", "9999999", "2026-11-05")
        self.assertEqual(status, lending.STATUS_INVALID)
        self.assertIn("borrower", errors)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM lendings").fetchone()[0], 0)

    def test_return_then_return_again_is_not_lent(self):
        lending.lend_equipment(self.conn, "A-1", "0000002", "2026-11-05")
        self.assertEqual(lending.return_equipment(self.conn, "A-1"), lending.STATUS_OK)
        self.assertEqual(lending.return_equipment(self.conn, "A-1"), lending.STATUS_NOT_LENT)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM lendings").fetchone()[0], 0)

    def test_return_missing_equipment_is_not_found(self):
        self.assertEqual(lending.return_equipment(self.conn, "NONE"), lending.STATUS_NOT_FOUND)

    def test_second_connection_sees_the_first_lend(self):
        # 別々の接続（別のリクエストに相当）でも、先の貸出が後の貸出で見える
        other = db.connect(self.data_dir)
        try:
            lending.lend_equipment(self.conn, "A-1", "0000002", "2026-11-05")
            _, status = lending.lend_equipment(other, "A-1", "0000001", "2026-11-05")
            self.assertEqual(status, lending.STATUS_ALREADY_LENT)
        finally:
            other.close()

    def test_concurrent_lends_record_exactly_one(self):
        # 2 つのスレッドが同時に同じ備品を貸し出しても、記録は 1 件だけ
        results = []
        barrier = threading.Barrier(2)

        def attempt(employee_number):
            conn = db.connect(self.data_dir)
            try:
                barrier.wait()
                results.append(lending.lend_equipment(conn, "A-1", employee_number, "2026-11-05")[1])
            finally:
                conn.close()

        threads = [
            threading.Thread(target=attempt, args=("0000001",)),
            threading.Thread(target=attempt, args=("0000002",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(results), [lending.STATUS_ALREADY_LENT, lending.STATUS_OK])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM lendings").fetchone()[0], 1)

    def test_today_jst_uses_japan_date(self):
        # UTC の 2026-11-04 15:00 は日本時間の 2026-11-05 00:00
        utc_time = datetime(2026, 11, 4, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(lending.today_jst(utc_time).isoformat(), "2026-11-05")
        before = datetime(2026, 11, 4, 14, 59, tzinfo=timezone.utc)
        self.assertEqual(lending.today_jst(before).isoformat(), "2026-11-04")
        self.assertIsNotNone(lending.today_jst())
        self.assertLessEqual(lending.today_jst(), lending.today_jst() + timedelta(days=1))

    def test_list_borrowers_is_sorted_by_employee_number(self):
        names = [row["employee_number"] for row in accounts.list_borrowers(self.conn)]
        self.assertEqual(names, ["0000001", "0000002"])


if __name__ == "__main__":
    unittest.main()

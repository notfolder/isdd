"""セッションの期限と作成・削除の単体テスト。"""

import unittest

from src import accounts, db, sessions
from tests.helpers import make_data_dir


class SessionsTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(make_data_dir())
        accounts.register_account(self.conn, "000001", "担当", "password1")

    def tearDown(self):
        self.conn.close()

    def test_valid_session_resolves_and_refreshes_last_seen(self):
        token = sessions.create_session(self.conn, "000001", now=1000.0)
        self.assertEqual(sessions.resolve_session(self.conn, token, 1800, now=1500.0), "000001")
        # 最後の操作が 1500 になったので、1500 + 1800 までは有効
        self.assertEqual(sessions.resolve_session(self.conn, token, 1800, now=3200.0), "000001")

    def test_idle_session_expires_and_is_deleted(self):
        token = sessions.create_session(self.conn, "000001", now=1000.0)
        self.assertIsNone(sessions.resolve_session(self.conn, token, 1800, now=2801.0))
        self.assertIsNone(sessions.resolve_session(self.conn, token, 1800, now=1001.0))

    def test_unknown_or_empty_token_is_none(self):
        self.assertIsNone(sessions.resolve_session(self.conn, None, 1800))
        self.assertIsNone(sessions.resolve_session(self.conn, "nope", 1800))

    def test_delete_session(self):
        token = sessions.create_session(self.conn, "000001", now=1000.0)
        sessions.delete_session(self.conn, token)
        self.assertIsNone(sessions.resolve_session(self.conn, token, 1800, now=1001.0))

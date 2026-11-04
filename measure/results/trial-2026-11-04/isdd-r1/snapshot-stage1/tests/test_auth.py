"""セッションの作成、無操作の期限切れ、ログアウトを確かめる。"""

from app import accounts, auth


def test_session_resolves_until_timeout(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    token = auth.create_session(conn, "100001")
    user = auth.resolve_session_user(conn, token, timeout_seconds=1800)
    assert user == {"employee_number": "100001", "name": "山田", "is_manager": True}


def test_idle_session_expires_and_is_removed(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    token = auth.create_session(conn, "100001")
    conn.execute("UPDATE sessions SET last_seen = last_seen - 100 WHERE token = ?", (token,))
    assert auth.resolve_session_user(conn, token, timeout_seconds=30) is None
    assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_logout_deletes_session(conn):
    accounts.register_account(conn, "100001", "山田", "password1")
    token = auth.create_session(conn, "100001")
    auth.delete_session(conn, token)
    assert auth.resolve_session_user(conn, token, timeout_seconds=1800) is None


def test_unknown_or_missing_token(conn):
    assert auth.resolve_session_user(conn, None, timeout_seconds=1800) is None
    assert auth.resolve_session_user(conn, "nope", timeout_seconds=1800) is None

"""セッションの作成・確認・削除。トークンはサーバー側の DB に保存する。"""

import secrets
import time


def create_session(conn, employee_number, now=None):
    """ログイン済みのセッションを作り、トークンを返す。

    トークンは 32 バイトの無作為の値を URL 安全な文字列にしたもの。
    引数 now は現在時刻（UNIX 秒）。省略時は現在時刻。
    """
    token = secrets.token_urlsafe(32)
    current = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        "INSERT INTO sessions (token, employee_number, last_seen) VALUES (?, ?, ?)",
        (token, employee_number, current),
    )
    conn.execute("COMMIT")
    return token


def resolve_session(conn, token, idle_timeout_seconds, now=None):
    """トークンから社員番号を求める。

    最後の操作から idle_timeout_seconds を超えていれば、セッションを削除して None を返す。
    有効なら最後の操作時刻を現在時刻に更新して社員番号を返す。トークンが無ければ None。
    """
    if not token:
        return None
    current = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute(
        "SELECT employee_number, last_seen FROM sessions WHERE token = ?", (token,)
    ).fetchone()
    if row is None:
        conn.execute("COMMIT")
        return None
    if current - row["last_seen"] > idle_timeout_seconds:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.execute("COMMIT")
        return None
    conn.execute("UPDATE sessions SET last_seen = ? WHERE token = ?", (current, token))
    conn.execute("COMMIT")
    return row["employee_number"]


def delete_session(conn, token):
    """トークンのセッションを削除する。無ければ何もしない。"""
    if not token:
        return
    conn.execute("BEGIN IMMEDIATE")
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.execute("COMMIT")

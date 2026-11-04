"""セッション、ログイン状態の解決、担当者の判定。

セッションは sessions 表に持つ。cookie には推測されないトークンだけを入れる。
最後の操作から設定秒数を過ぎたセッションは削除し、未ログインとして扱う。
"""

import secrets
import time
from functools import wraps

from flask import flash, g, redirect, url_for

SESSION_COOKIE = "isdd_session"


def create_session(conn, employee_number: str) -> str:
    """ログインした社員のセッションを作り、cookie に入れるトークンを返す。"""
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO sessions (token, employee_number, last_seen) VALUES (?, ?, ?)",
        (token, employee_number, time.time()),
    )
    return token


def resolve_session_user(conn, token: str | None, timeout_seconds: int) -> dict | None:
    """トークンからログイン中の社員を返す。未ログイン・期限切れなら None。

    期限内なら最後の操作の時刻を今に更新する。期限切れのセッションは削除する。
    """
    if not token:
        return None
    row = conn.execute(
        "SELECT s.employee_number, s.last_seen, a.name, a.is_manager "
        "FROM sessions s JOIN accounts a ON a.employee_number = s.employee_number "
        "WHERE s.token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    now = time.time()
    if now - row["last_seen"] > timeout_seconds:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        return None
    conn.execute("UPDATE sessions SET last_seen = ? WHERE token = ?", (now, token))
    return {
        "employee_number": row["employee_number"],
        "name": row["name"],
        "is_manager": bool(row["is_manager"]),
    }


def delete_session(conn, token: str | None) -> None:
    """セッションを削除する（ログアウト）。無ければ何もしない。"""
    if token:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def require_manager(view):
    """担当者だけが呼べる画面・操作に付ける。

    未ログインはログイン画面へ移す。社員は貸出状況の画面へ戻し、「この操作は担当者だけが行えます」を出す。
    呼び出し元は g.current_user を設定しておく。
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = g.get("current_user")
        if user is None:
            return redirect(url_for("ledger.login"))
        if not user["is_manager"]:
            flash("この操作は担当者だけが行えます", "message")
            return redirect(url_for("ledger.lending_status"))
        return view(*args, **kwargs)

    return wrapper

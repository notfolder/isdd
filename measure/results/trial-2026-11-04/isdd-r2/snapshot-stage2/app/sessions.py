"""ログイン状態（セッション）の作成、確認、削除と、担当者の検査。

セッションは sessions 表に持つ。最終操作からの秒数が上限を超えたら無効にする。
"""

import sqlite3
from typing import Optional

from app.security import new_session_token


def create_session(conn: sqlite3.Connection, employee_number: str, now: int) -> str:
    """ログイン成功時に新しいセッションを作る。

    Args:
        conn: DB 接続。
        employee_number: ログインしたアカウントの社員番号。
        now: 現在の UNIX 秒。

    Returns:
        Cookie に入れるトークン。
    """
    token = new_session_token()
    conn.execute(
        "INSERT INTO sessions (token, employee_number, last_seen) VALUES (?, ?, ?)",
        (token, employee_number, now),
    )
    return token


def resolve_session(
    conn: sqlite3.Connection, token: Optional[str], timeout_seconds: int, now: int
) -> Optional[dict]:
    """トークンから今のログイン者を得る。期限切れなら行を消して None を返す。

    有効なら最終操作時刻を今に更新する。

    Args:
        conn: DB 接続。
        token: Cookie のトークン。無ければ None。
        timeout_seconds: 自動ログアウトまでの秒数。
        now: 現在の UNIX 秒。

    Returns:
        社員番号、名前、役割を持つ dict。未ログインなら None。
    """
    if not token:
        return None
    row = conn.execute(
        "SELECT s.last_seen, a.employee_number, a.name, a.role "
        "FROM sessions s JOIN accounts a ON a.employee_number = s.employee_number "
        "WHERE s.token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    if now - row["last_seen"] > timeout_seconds:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        return None
    conn.execute("UPDATE sessions SET last_seen = ? WHERE token = ?", (now, token))
    return {
        "employee_number": row["employee_number"],
        "name": row["name"],
        "role": row["role"],
    }


def delete_session(conn: sqlite3.Connection, token: Optional[str]) -> None:
    """ログアウト時にセッションを消す。

    Args:
        conn: DB 接続。
        token: Cookie のトークン。無ければ何もしない。
    """
    if token:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def require_manager(user: Optional[dict]) -> Optional[str]:
    """担当者の操作として許されるかを検査する。

    Args:
        user: 今のログイン者（resolve_session の結果）。未ログインなら None。

    Returns:
        未ログインなら "login"、社員なら "forbidden"、担当者なら None。
    """
    if user is None:
        return "login"
    if user["role"] != "manager":
        return "forbidden"
    return None

"""ログイン状態の管理と、担当者だけの操作の拒否。"""

import time
from functools import wraps
from typing import Any, Callable, Optional

from flask import flash, redirect, session, url_for

from .core.accounts import ROLE_MANAGER

SESSION_KEY = "user"
DENY_MESSAGE = "この操作は担当者だけが行えます"


def log_in_user(employee_number: str, name: str, role: str) -> None:
    """セッションを作り直し、社員番号・名前・役割と最終操作時刻を入れる。"""
    session.clear()
    session[SESSION_KEY] = {
        "employee_number": employee_number,
        "name": name,
        "role": role,
        "last_active": time.time(),
    }


def log_out_user() -> None:
    """セッションを消す。"""
    session.clear()


def current_user() -> Optional[dict[str, str]]:
    """ログイン中の社員の社員番号・名前・役割を返す。未ログインなら None。"""
    user = session.get(SESSION_KEY)
    if user is None:
        return None
    return {k: user[k] for k in ("employee_number", "name", "role")}


def sync_session_user(conn: Any) -> None:
    """要求ごとに、セッションの社員を DB の現在の状態に合わせる。

    アカウントが削除されていればセッションを消す（未ログイン扱い）。あれば名前と権限を入れ直す。
    """
    user = session.get(SESSION_KEY)
    if user is None:
        return
    row = conn.execute(
        "SELECT name, role FROM account WHERE employee_number = ?", (user["employee_number"],)
    ).fetchone()
    if row is None:
        session.clear()
        return
    user["name"] = row["name"]
    user["role"] = row["role"]
    session[SESSION_KEY] = user


def check_idle_timeout(timeout_seconds: int, now: float) -> None:
    """無操作の時間を確かめる。超えていればセッションを消す。超えていなければ最終操作時刻を更新する。"""
    user = session.get(SESSION_KEY)
    if user is None:
        return
    if now - user.get("last_active", 0) > timeout_seconds:
        session.clear()
        return
    user["last_active"] = now
    session[SESSION_KEY] = user


def require_manager(view: Callable[..., Any]) -> Callable[..., Any]:
    """担当者だけが通せる画面・操作にする。担当者でなければ要求を拒否し、理由を `.message` に出す。

    未ログインはログイン画面へ、社員は貸出状況の画面へ戻す。
    """

    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = current_user()
        if user is None:
            flash(DENY_MESSAGE, "message")
            return redirect(url_for("ledger.login"))
        if user["role"] != ROLE_MANAGER:
            flash(DENY_MESSAGE, "message")
            return redirect(url_for("ledger.status"))
        return view(*args, **kwargs)

    return wrapper

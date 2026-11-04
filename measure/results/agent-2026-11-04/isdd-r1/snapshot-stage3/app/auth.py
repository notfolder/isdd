"""セッションによるログイン・ログアウト、利用者の判定、担当者の確認。"""

import sqlite3
import time
from typing import Dict, Optional

from flask import Response, current_app, flash, g, redirect, session, url_for

from . import accounts

ROLE_MANAGER = "manager"
SESSION_ACCOUNT_KEY = "account"
SESSION_LAST_ACTIVE_KEY = "last_active"

MSG_MANAGER_ONLY = "この操作は担当者だけが行えます"
MSG_IDLE_LOGOUT = "一定時間操作がなかったため、ログアウトしました"


def login_user(account: Dict[str, object]) -> None:
    """利用者をセッションに入れる。以前のセッションは捨てる。"""
    session.clear()
    session[SESSION_ACCOUNT_KEY] = {
        "id": account["id"],
        "name": account["name"],
        "role": account["role"],
    }
    session[SESSION_LAST_ACTIVE_KEY] = int(time.time())


def logout_user() -> None:
    """セッションを消す。"""
    session.clear()


def load_current_user(conn: sqlite3.Connection) -> None:
    """要求ごとに呼ぶ。制限時間を超えていればセッションを消し、未ログインとして扱う。

    制限時間内なら、セッションの利用者を DB のアカウントで引き直す。アカウントが無ければ（削除された）
    セッションを消す。役割はセッションの値を使わず DB の値を使う（担当者から外された人の古いセッションで
    担当者の操作をさせないため）。最後の操作の時刻を今に更新し、利用者を g.account に入れる。
    """
    g.account = None
    if SESSION_ACCOUNT_KEY not in session:
        return
    timeout = _idle_timeout_seconds()
    now = int(time.time())
    last_active = int(session.get(SESSION_LAST_ACTIVE_KEY, 0))
    if now - last_active > timeout:
        session.clear()
        flash(MSG_IDLE_LOGOUT)
        return
    stored = session[SESSION_ACCOUNT_KEY]
    account = accounts.find_account_by_id(conn, int(stored["id"]))
    if account is None:
        session.clear()
        return
    session[SESSION_LAST_ACTIVE_KEY] = now
    session[SESSION_ACCOUNT_KEY] = account
    g.account = account


def require_manager() -> Optional[Response]:
    """担当者でなければ拒否の応答を返す。担当者なら None を返す。

    未ログインはログイン画面へ送る。社員は貸出状況の画面に戻し、知らせを出す。
    """
    if g.account is None:
        return redirect(url_for("web.login"))
    if g.account["role"] != ROLE_MANAGER:
        flash(MSG_MANAGER_ONLY)
        return redirect(url_for("web.loan_status"))
    return None


def _idle_timeout_seconds() -> int:
    return int(current_app.config["IDLE_TIMEOUT_SECONDS"])

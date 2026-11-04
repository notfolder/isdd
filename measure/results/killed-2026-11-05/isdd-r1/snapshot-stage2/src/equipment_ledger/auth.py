"""ログイン状態、無操作の期限切れ、担当者の判定。

ログイン状態は Flask の署名付き Cookie のセッションに持つ。
セッションにはアカウントの識別子と最後の操作の時刻だけを入れる。
"""

import functools
import time

from flask import flash, redirect, session, url_for

from equipment_ledger.db import get_db

SESSION_ACCOUNT_KEY = "account_id"
SESSION_LAST_SEEN_KEY = "last_seen"
MANAGER_ONLY_MESSAGE = "この操作は担当者だけが行えます"
SESSION_EXPIRED_MESSAGE = "セッションの有効期限が切れました。ログインしてください"


def log_in(account_id):
    """ログインする。古いセッションは捨てて、アカウントの識別子と現在時刻を入れる。"""
    session.clear()
    session[SESSION_ACCOUNT_KEY] = account_id
    session[SESSION_LAST_SEEN_KEY] = time.time()


def log_out():
    """ログアウトする。セッションを空にする。"""
    session.clear()


def current_account():
    """ログイン中のアカウントの行を返す。未ログインなら None を返す。"""
    account_id = session.get(SESSION_ACCOUNT_KEY)
    if account_id is None:
        return None
    return get_db().execute(
        "SELECT id, employee_number, name, role FROM accounts WHERE id = ?",
        (account_id,),
    ).fetchone()


def expire_idle_session(idle_timeout_seconds):
    """無操作の期限を確かめる。期限を過ぎていればセッションを捨てて True を返す。

    期限内なら最後の操作の時刻を今に更新して False を返す。ログインしていなければ何もしない。
    """
    if SESSION_ACCOUNT_KEY not in session:
        return False
    now = time.time()
    if now - session.get(SESSION_LAST_SEEN_KEY, 0) > idle_timeout_seconds:
        session.clear()
        flash(SESSION_EXPIRED_MESSAGE, "message")
        return True
    session[SESSION_LAST_SEEN_KEY] = now
    return False


def require_manager(view):
    """担当者だけが呼べる画面・操作を包む。

    未ログインはログイン画面へ、社員は貸出状況の画面へ転送し、どちらも担当者だけの文言を出す。
    """

    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        account = current_account()
        if account is None:
            flash(MANAGER_ONLY_MESSAGE, "message")
            return redirect(url_for("ledger.login"))
        if account["role"] != "manager":
            flash(MANAGER_ONLY_MESSAGE, "message")
            return redirect(url_for("ledger.equipment_status"))
        return view(*args, **kwargs)

    return wrapper

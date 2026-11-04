"""セッションとロールの判定。"""

import time
from functools import wraps

from flask import current_app, flash, redirect, session, url_for

from .accounts import ROLE_MANAGER, get_account

SESSION_ACCOUNT_KEY = "account_id"
SESSION_LAST_ACTIVE_KEY = "last_active"
MSG_MANAGER_ONLY = "この操作は担当者だけが行えます"


def login_account(account_id):
    """アカウントをログイン状態にする。最後の操作時刻も記録する。"""
    session.clear()
    session[SESSION_ACCOUNT_KEY] = account_id
    session[SESSION_LAST_ACTIVE_KEY] = time.time()


def logout_account():
    """セッションを消してログアウトする。"""
    session.clear()


def current_account():
    """ログイン中のアカウントを返す。ログインしていなければ None。"""
    account_id = session.get(SESSION_ACCOUNT_KEY)
    if account_id is None:
        return None
    return get_account(account_id)


def check_idle_timeout():
    """要求ごとに呼ぶ。最後の操作から設定秒数を超えていればセッションを消し、そうでなければ時刻を更新する。"""
    if SESSION_ACCOUNT_KEY not in session:
        return
    now = time.time()
    limit = current_app.config["SESSION_IDLE_TIMEOUT_SECONDS"]
    if now - session.get(SESSION_LAST_ACTIVE_KEY, 0) > limit:
        session.clear()
    else:
        session[SESSION_LAST_ACTIVE_KEY] = now


def manager_required(view):
    """担当者だけが呼べる画面・操作に付ける。

    未ログインはログイン画面へ、社員は貸出状況の画面へ戻し、どちらも MSG_MANAGER_ONLY を出す。
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        account = current_account()
        if account is None:
            flash(MSG_MANAGER_ONLY)
            return redirect(url_for("main.login_page"))
        if account["role"] != ROLE_MANAGER:
            flash(MSG_MANAGER_ONLY)
            return redirect(url_for("main.index_page"))
        return view(*args, **kwargs)

    return wrapper

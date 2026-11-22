"""ログイン状態の取り出しと、セッションの開始・終了。認証の判定はこのファイルに集める。"""

from typing import Optional

from flask import current_app, g, session

from service.accounts import User

SESSION_USER_KEY = "user_id"


def current_user() -> Optional[User]:
    """セッションの利用者を返す。未ログインや利用者が無い場合は None。同じ要求の中では 1 回だけ探す。"""
    if "current_user" in g:
        return g.current_user
    user: Optional[User] = None
    user_id = session.get(SESSION_USER_KEY)
    if user_id is not None:
        user = current_app.extensions["services"].accounts.find_by_id(int(user_id))
    g.current_user = user
    return user


def start_session(user: User) -> None:
    """ログインした利用者をセッションに入れる。ブラウザを閉じると切れる（永続化しない）。"""
    session.clear()
    session[SESSION_USER_KEY] = user.id
    session.permanent = False


def end_session() -> None:
    """セッションを空にしてログアウトする。"""
    session.clear()

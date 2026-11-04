"""現在の利用者の取得と、担当者かどうかの判定。"""

from src import sessions
from src.accounts import ROLE_MANAGER

ACCESS_OK = "ok"
ACCESS_LOGIN_REQUIRED = "login_required"
ACCESS_MANAGER_ONLY = "manager_only"


def current_user(conn, token, idle_timeout_seconds, now=None):
    """Cookie のトークンから現在の利用者を求める。

    戻り値は社員番号・名前・役割を持つ辞書。未ログイン、または期限切れなら None。
    """
    employee_number = sessions.resolve_session(conn, token, idle_timeout_seconds, now)
    if employee_number is None:
        return None
    row = conn.execute(
        "SELECT employee_number, name, role FROM accounts WHERE employee_number = ?",
        (employee_number,),
    ).fetchone()
    if row is None:
        return None
    return {
        "employee_number": row["employee_number"],
        "name": row["name"],
        "role": row["role"],
    }


def require_manager(user):
    """備品の登録・修正・削除を許可してよいかを判定する。

    戻り値は ACCESS_OK（担当者）、ACCESS_LOGIN_REQUIRED（未ログイン）、
    ACCESS_MANAGER_ONLY（社員）のいずれか。
    """
    if user is None:
        return ACCESS_LOGIN_REQUIRED
    if user["role"] != ROLE_MANAGER:
        return ACCESS_MANAGER_ONLY
    return ACCESS_OK

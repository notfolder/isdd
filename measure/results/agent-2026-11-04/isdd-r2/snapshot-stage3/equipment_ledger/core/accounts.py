"""社員アカウントの登録と照合。"""

import sqlite3
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

ROLE_MANAGER = "manager"
ROLE_MEMBER = "member"

# 存在しない社員番号でも照合の時間を揃えるための比較用ハッシュ。
_DUMMY_HASH = generate_password_hash("dummy-password-for-timing")


def register_account(
    conn: sqlite3.Connection, employee_number: str, name: str, password: str
) -> Optional[str]:
    """アカウントを登録する。

    件数の確認と挿入を 1 つの即時トランザクションで行い、0 件のときだけ担当者にする。
    登録できたら役割（manager か member）を返し、社員番号が重複したら None を返す。
    """
    password_hash = generate_password_hash(password)
    conn.execute("BEGIN IMMEDIATE")
    try:
        count = conn.execute("SELECT COUNT(*) FROM account").fetchone()[0]
        role = ROLE_MANAGER if count == 0 else ROLE_MEMBER
        conn.execute(
            "INSERT INTO account (employee_number, name, password_hash, role) VALUES (?, ?, ?, ?)",
            (employee_number, name, password_hash, role),
        )
        conn.execute("COMMIT")
        return role
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        return None
    except Exception:
        conn.execute("ROLLBACK")
        raise


def authenticate(
    conn: sqlite3.Connection, employee_number: str, password: str
) -> Optional[dict[str, str]]:
    """社員番号とパスワードを照合する。成功なら社員番号・名前・役割の辞書、失敗なら None を返す。

    社員番号が無い場合も同じ照合の処理を行い、失敗の理由を外から区別できないようにする。
    """
    row = conn.execute(
        "SELECT employee_number, name, password_hash, role FROM account WHERE employee_number = ?",
        (employee_number,),
    ).fetchone()
    if row is None:
        check_password_hash(_DUMMY_HASH, password)
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return {"employee_number": row["employee_number"], "name": row["name"], "role": row["role"]}


def list_borrower_candidates(conn: sqlite3.Connection) -> list[dict[str, str]]:
    """貸出の登録で選べる社員を社員番号の昇順に返す（社員番号と名前）。"""
    rows = conn.execute("SELECT employee_number, name FROM account ORDER BY employee_number ASC").fetchall()
    return [{"employee_number": row["employee_number"], "name": row["name"]} for row in rows]


ROLE_CHANGE_OK = "changed"
ROLE_NO_ACCOUNT = "no_account"
ROLE_LAST_MANAGER = "last_manager"

RESET_OK = "reset"
RESET_NO_ACCOUNT = "no_account"

DELETE_OK = "deleted"
DELETE_NO_ACCOUNT = "no_account"
DELETE_LENT = "lent"
DELETE_LAST_MANAGER = "last_manager"


def list_accounts(conn: sqlite3.Connection) -> list[dict[str, str]]:
    """全アカウントを社員番号の昇順に返す（社員番号・名前・権限。パスワードは返さない）。"""
    rows = conn.execute(
        "SELECT employee_number, name, role FROM account ORDER BY employee_number ASC"
    ).fetchall()
    return [{"employee_number": r["employee_number"], "name": r["name"], "role": r["role"]} for r in rows]


def _manager_count(conn: sqlite3.Connection) -> int:
    """担当者の人数を数える（呼び出し側のトランザクションの中で使う）。"""
    return conn.execute("SELECT COUNT(*) FROM account WHERE role = ?", (ROLE_MANAGER,)).fetchone()[0]


def change_account_role(conn: sqlite3.Connection, employee_number: str, new_role: str) -> str:
    """権限を変える。担当者を社員にするときは、担当者の数を同じトランザクションで数え、1 人だけなら拒否する。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT role FROM account WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            return ROLE_NO_ACCOUNT
        if new_role == ROLE_MEMBER and row["role"] == ROLE_MANAGER and _manager_count(conn) <= 1:
            conn.execute("ROLLBACK")
            return ROLE_LAST_MANAGER
        conn.execute("UPDATE account SET role = ? WHERE employee_number = ?", (new_role, employee_number))
        conn.execute("COMMIT")
        return ROLE_CHANGE_OK
    except Exception:
        conn.execute("ROLLBACK")
        raise


def reset_password(conn: sqlite3.Connection, employee_number: str, password: str) -> str:
    """パスワードのハッシュを置き換える。古いハッシュは残らない。対象が無ければ RESET_NO_ACCOUNT。"""
    cursor = conn.execute(
        "UPDATE account SET password_hash = ? WHERE employee_number = ?",
        (generate_password_hash(password), employee_number),
    )
    return RESET_OK if cursor.rowcount == 1 else RESET_NO_ACCOUNT


def delete_account(conn: sqlite3.Connection, employee_number: str) -> str:
    """アカウントを物理削除する。借りている社員、最後の担当者、対象無しは拒否の結果を返す。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT role FROM account WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            return DELETE_NO_ACCOUNT
        lent = conn.execute(
            "SELECT 1 FROM lending WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if lent is not None:
            conn.execute("ROLLBACK")
            return DELETE_LENT
        if row["role"] == ROLE_MANAGER and _manager_count(conn) <= 1:
            conn.execute("ROLLBACK")
            return DELETE_LAST_MANAGER
        conn.execute("DELETE FROM account WHERE employee_number = ?", (employee_number,))
        conn.execute("COMMIT")
        return DELETE_OK
    except Exception:
        conn.execute("ROLLBACK")
        raise

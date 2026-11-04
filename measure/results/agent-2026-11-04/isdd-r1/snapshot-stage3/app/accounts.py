"""アカウントの登録と照合、一覧、役割の変更、パスワードの再設定、削除。"""

import sqlite3
from typing import Dict, List, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from .validation import MSG_EMPLOYEE_NUMBER_DUPLICATE, validate_account_input

ROLE_MANAGER = "manager"
ROLE_MEMBER = "member"

ACCOUNT_OK = "ok"
ACCOUNT_NOT_FOUND = "not_found"
ACCOUNT_LAST_MANAGER = "last_manager"
ACCOUNT_BORROWING = "borrowing"


def register_account(
    conn: sqlite3.Connection, employee_number: str, name: str, password: str
) -> Dict[str, str]:
    """アカウントを登録する。最初の 1 件は担当者、2 件目以降は社員になる。

    戻り値は入力欄名から文言への辞書で、空なら登録できた。書き込みのトランザクションを
    先に開き、件数の確認と挿入を同じ区切りで行う（同時の登録でも担当者は 1 件だけになる）。
    """
    errors = validate_account_input(employee_number, name, password)
    name = name.strip()
    conn.execute("BEGIN IMMEDIATE")
    try:
        if "employee_number" not in errors:
            exists = conn.execute(
                "SELECT 1 FROM accounts WHERE employee_number = ?", (employee_number,)
            ).fetchone()
            if exists is not None:
                errors["employee_number"] = MSG_EMPLOYEE_NUMBER_DUPLICATE
        if errors:
            conn.execute("ROLLBACK")
            return errors
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        role = ROLE_MANAGER if count == 0 else ROLE_MEMBER
        conn.execute(
            "INSERT INTO accounts (employee_number, name, password_hash, role) VALUES (?, ?, ?, ?)",
            (employee_number, name, generate_password_hash(password), role),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        return {"employee_number": MSG_EMPLOYEE_NUMBER_DUPLICATE}
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {}


def authenticate_account(
    conn: sqlite3.Connection, employee_number: str, password: str
) -> Optional[Dict[str, object]]:
    """社員番号とパスワードが一致するアカウントを返す。一致しなければ None（理由は区別しない）。"""
    row = conn.execute(
        "SELECT id, name, role, password_hash FROM accounts WHERE employee_number = ?",
        (employee_number,),
    ).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return None
    return {"id": row["id"], "name": row["name"], "role": row["role"]}


def list_accounts(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    """全アカウントを社員番号の昇順で返す（社員番号、名前、役割）。"""
    rows = conn.execute(
        "SELECT employee_number, name, role FROM accounts ORDER BY employee_number ASC"
    ).fetchall()
    return [
        {"employee_number": r["employee_number"], "name": r["name"], "role": r["role"]}
        for r in rows
    ]


def find_account_by_id(conn: sqlite3.Connection, account_id: int) -> Optional[Dict[str, object]]:
    """内部の識別子で 1 件引く。無ければ None（削除された、または存在しない）。"""
    row = conn.execute(
        "SELECT id, name, role FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "role": row["role"]}


def _count_managers(conn: sqlite3.Connection) -> int:
    return int(
        conn.execute("SELECT COUNT(*) FROM accounts WHERE role = ?", (ROLE_MANAGER,)).fetchone()[0]
    )


def change_account_role(conn: sqlite3.Connection, employee_number: str, role: str) -> str:
    """役割を変える。担当者を外す操作で担当者が 1 人だけなら変えない。結果は ACCOUNT_* のいずれか。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT role FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            return ACCOUNT_NOT_FOUND
        if role == ROLE_MEMBER and row["role"] == ROLE_MANAGER and _count_managers(conn) <= 1:
            conn.execute("ROLLBACK")
            return ACCOUNT_LAST_MANAGER
        conn.execute("UPDATE accounts SET role = ? WHERE employee_number = ?", (role, employee_number))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return ACCOUNT_OK


def reset_account_password(conn: sqlite3.Connection, employee_number: str, password: str) -> str:
    """パスワードを新しいものに置き換える（古いパスワードは使えなくなる）。結果は ACCOUNT_* のいずれか。

    入力の検査は呼び出し側で行う。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        cursor = conn.execute(
            "UPDATE accounts SET password_hash = ? WHERE employee_number = ?",
            (generate_password_hash(password), employee_number),
        )
        if cursor.rowcount == 0:
            conn.execute("ROLLBACK")
            return ACCOUNT_NOT_FOUND
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return ACCOUNT_OK


def delete_account(conn: sqlite3.Connection, employee_number: str) -> str:
    """アカウントを行ごと削除する。借りている備品がある社員と、最後の担当者は削除しない。

    結果は ACCOUNT_* のいずれか。貸出の有無と担当者の人数は、削除と同じトランザクションで確かめる。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT id, role FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            return ACCOUNT_NOT_FOUND
        loaned = conn.execute(
            "SELECT 1 FROM loans WHERE account_id = ?", (row["id"],)
        ).fetchone()
        if loaned is not None:
            conn.execute("ROLLBACK")
            return ACCOUNT_BORROWING
        if row["role"] == ROLE_MANAGER and _count_managers(conn) <= 1:
            conn.execute("ROLLBACK")
            return ACCOUNT_LAST_MANAGER
        conn.execute("DELETE FROM accounts WHERE id = ?", (row["id"],))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return ACCOUNT_OK

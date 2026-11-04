"""アカウントの登録と照合。"""

import sqlite3
from typing import Dict, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from .validation import MSG_EMPLOYEE_NUMBER_DUPLICATE, validate_account_input

ROLE_MANAGER = "manager"
ROLE_MEMBER = "member"


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

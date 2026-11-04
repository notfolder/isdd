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

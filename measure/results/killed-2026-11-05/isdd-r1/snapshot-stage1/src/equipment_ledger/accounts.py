"""アカウントの登録と認証。"""

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

DUPLICATE_EMPLOYEE_MESSAGE = "この社員番号は既に登録されています"


def register_account(conn, employee_number, name, password):
    """アカウントを登録する。最初の 1 件は担当者、2 件目以降は社員にする。

    件数の確認と挿入は書き込みロック付きのトランザクションで行い、同時に来ても担当者は 1 人だけになる。
    戻り値は (役割, 文言)。成功なら役割（manager か employee）と None、社員番号が重複なら None と文言。
    """
    password_hash = generate_password_hash(password)
    try:
        conn.execute("BEGIN IMMEDIATE")
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        role = "manager" if count == 0 else "employee"
        conn.execute(
            "INSERT INTO accounts (employee_number, name, password_hash, role) VALUES (?, ?, ?, ?)",
            (employee_number, name, password_hash, role),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        _rollback(conn)
        return None, DUPLICATE_EMPLOYEE_MESSAGE
    except BaseException:
        _rollback(conn)
        raise
    return role, None


def find_account(conn, employee_number):
    """社員番号でアカウントを 1 件探す。無ければ None を返す。"""
    return conn.execute(
        "SELECT id, employee_number, name, password_hash, role FROM accounts WHERE employee_number = ?",
        (employee_number,),
    ).fetchone()


def authenticate_account(conn, employee_number, password):
    """社員番号とパスワードを照合する。合えばアカウントの行、違えば None を返す。

    どちらが違うかは返さない（呼び出し側は同じ文言を出す）。
    """
    account = find_account(conn, employee_number)
    if account is None:
        return None
    if not check_password_hash(account["password_hash"], password):
        return None
    return account


def _rollback(conn):
    if conn.in_transaction:
        conn.execute("ROLLBACK")

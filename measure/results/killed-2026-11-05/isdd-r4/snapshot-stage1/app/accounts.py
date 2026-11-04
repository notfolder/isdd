"""アカウントの登録・認証・取り出し。"""

import re
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{6}")
NAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
ROLE_MANAGER = "manager"
ROLE_EMPLOYEE = "employee"


def hash_password(password):
    """パスワードをハッシュ値にする。

    引数: password（平文）。戻り値: 保存用のハッシュ文字列。
    """
    return generate_password_hash(password)


def validate_registration(employee_number, name, password):
    """登録の入力を検査する。

    引数: employee_number（社員番号）、name（前後の空白を取った名前）、password（パスワード）。
    戻り値: 入力欄の名前をキーにした、エラー文言の辞書（問題が無ければ空）。
    """
    errors = {}
    if not EMPLOYEE_NUMBER_PATTERN.fullmatch(employee_number):
        errors["employee_number"] = "社員番号は 6 桁の数字で入力してください"
    if name == "":
        errors["name"] = "名前を入力してください"
    elif len(name) > NAME_MAX_LENGTH:
        errors["name"] = "名前は 30 文字以内で入力してください"
    if len(password) < PASSWORD_MIN_LENGTH:
        errors["password"] = "パスワードは 8 文字以上で入力してください"
    return errors


def register_account(employee_number, name, password):
    """アカウントを 1 件登録する。アカウントが 0 件なら担当者、それ以外は社員にする。

    件数の確認と挿入は 1 つの即時書き込みトランザクションで行い、同時の登録でも担当者は 1 件になる。
    引数: employee_number、name（検査済み）、password（平文）。
    戻り値: (登録したアカウントの id, エラーの辞書)。失敗時は id が None。
    """
    conn = get_db()
    password_hash = hash_password(password)
    conn.execute("BEGIN IMMEDIATE")
    try:
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        role = ROLE_MANAGER if count == 0 else ROLE_EMPLOYEE
        cur = conn.execute(
            "INSERT INTO accounts (employee_number, name, password_hash, role) VALUES (?, ?, ?, ?)",
            (employee_number, name, password_hash, role),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        return None, {"employee_number": "この社員番号は既に登録されています"}
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return cur.lastrowid, {}


def get_account(account_id):
    """id でアカウントを 1 件取り出す。無ければ None。

    戻り値: id・employee_number・name・role を持つ辞書、または None。
    """
    row = get_db().execute(
        "SELECT id, employee_number, name, role FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    return dict(row) if row is not None else None


def authenticate_account(employee_number, password):
    """社員番号とパスワードが合うアカウントを返す。合わなければ None。

    どちらが違うかは区別しない（呼び出し側の文言も 1 つだけにする）。
    """
    row = get_db().execute(
        "SELECT id, password_hash FROM accounts WHERE employee_number = ?", (employee_number,)
    ).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return None
    return get_account(row["id"])

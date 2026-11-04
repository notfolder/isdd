"""アカウントの登録、認証、一覧、担当者の付け外し、パスワード再設定、削除。

書き込みは BEGIN IMMEDIATE のトランザクションで行い、人数の数えと更新を一体にする。
業務エラーは (表示の種類, 入力欄の id, 文言) の組で返す。表示の種類は
field（入力欄）、error（画面全体）、message（結果の知らせ）。
"""

import sqlite3
from typing import Optional, Tuple

from app import validation
from app.security import hash_password, verify_password

MAX_ACCOUNTS = 50
ROLE_MANAGER = "manager"
ROLE_MEMBER = "member"
LAST_MANAGER_TEXT = "担当者が 1 人もいなくなるため、この操作はできません"
BORROWED_TEXT = "この社員は備品を借りているため削除できません。先に返却を処理してください"

Problem = Tuple[str, Optional[str], str]


def _finish(conn: sqlite3.Connection, ok: bool) -> None:
    conn.execute("COMMIT" if ok else "ROLLBACK")


def _manager_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM accounts WHERE role = ?", (ROLE_MANAGER,)).fetchone()
    return int(row["n"])


def register_account(
    conn: sqlite3.Connection, employee_number: str, name: str, password: str
) -> Optional[Problem]:
    """アカウントを登録する。最初の 1 件は担当者、2 件目以降は社員になる。

    Args:
        conn: DB 接続。
        employee_number: 社員番号（6 桁の数字）。
        name: 名前（30 文字以内）。
        password: パスワード（8 文字以上）。平文は保存せずハッシュにする。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    checks = [
        ("id_employee_number", validation.validate_employee_number(employee_number)),
        ("id_name", validation.validate_name(name)),
        ("id_password", validation.validate_password(password)),
    ]
    for field, text in checks:
        if text is not None:
            return ("field", field, text)
    duplicate = ("field", "id_employee_number", "この社員番号は既に登録されています")
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        exists = conn.execute(
            "SELECT 1 FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if exists is not None:
            return duplicate
        count = conn.execute("SELECT COUNT(*) AS n FROM accounts").fetchone()["n"]
        if count >= MAX_ACCOUNTS:
            return ("error", None, "利用者は 50 人までのため、登録できません")
        role = ROLE_MANAGER if count == 0 else ROLE_MEMBER
        try:
            conn.execute(
                "INSERT INTO accounts (employee_number, name, password_hash, role) VALUES (?, ?, ?, ?)",
                (employee_number, name.strip(), hash_password(password), role),
            )
        except sqlite3.IntegrityError:
            return duplicate
        ok = True
        return None
    finally:
        _finish(conn, ok)


def authenticate_account(conn: sqlite3.Connection, employee_number: str, password: str) -> Optional[str]:
    """社員番号とパスワードを照合する。

    どちらが違うかは示さない。形式が不正な社員番号は照合せず失敗にする。

    Args:
        conn: DB 接続。
        employee_number: 入力された社員番号。
        password: 入力されたパスワード。

    Returns:
        一致すれば社員番号。失敗なら None。
    """
    if validation.validate_employee_number(employee_number) is not None:
        return None
    row = conn.execute(
        "SELECT password_hash FROM accounts WHERE employee_number = ?", (employee_number,)
    ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return employee_number


def list_accounts(conn: sqlite3.Connection) -> list:
    """全アカウントを社員番号の昇順で返す。

    Args:
        conn: DB 接続。

    Returns:
        社員番号、名前、役割（manager または member）を持つ dict のリスト。
    """
    rows = conn.execute(
        "SELECT employee_number, name, role FROM accounts ORDER BY employee_number"
    ).fetchall()
    return [dict(row) for row in rows]


def change_manager_role(conn: sqlite3.Connection, employee_number: str, make_manager: bool) -> Optional[Problem]:
    """社員を担当者にする、または担当者を社員に戻す。担当者が 0 人になる操作は拒否する。

    Args:
        conn: DB 接続。
        employee_number: 対象の社員番号。
        make_manager: True なら担当者にし、False なら社員に戻す。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        row = conn.execute("SELECT role FROM accounts WHERE employee_number = ?", (employee_number,)).fetchone()
        if row is None:
            return ("error", None, "対象のアカウントが見つかりません")
        if not make_manager and row["role"] == ROLE_MANAGER and _manager_count(conn) <= 1:
            return ("error", None, LAST_MANAGER_TEXT)
        role = ROLE_MANAGER if make_manager else ROLE_MEMBER
        conn.execute("UPDATE accounts SET role = ? WHERE employee_number = ?", (role, employee_number))
        ok = True
        return None
    finally:
        _finish(conn, ok)


def reset_password(conn: sqlite3.Connection, employee_number: str, new_password: str) -> Optional[Problem]:
    """社員のパスワードを再設定する。

    Args:
        conn: DB 接続。
        employee_number: 対象の社員番号。
        new_password: 新しいパスワード（8 文字以上）。

    Returns:
        成功なら None。失敗なら業務エラーの組（入力欄は new_password）。
    """
    text = validation.validate_password(new_password)
    if text is not None:
        return ("field", "new_password", text)
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        row = conn.execute("SELECT 1 FROM accounts WHERE employee_number = ?", (employee_number,)).fetchone()
        if row is None:
            return ("error", None, "対象のアカウントが見つかりません")
        conn.execute(
            "UPDATE accounts SET password_hash = ? WHERE employee_number = ?",
            (hash_password(new_password), employee_number),
        )
        ok = True
        return None
    finally:
        _finish(conn, ok)


def delete_account(conn: sqlite3.Connection, employee_number: str) -> Optional[Problem]:
    """アカウントを削除する。備品を借りている社員と、最後の担当者は削除できない。

    削除するアカウントのセッションも消す。

    Args:
        conn: DB 接続。
        employee_number: 対象の社員番号。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        row = conn.execute("SELECT role FROM accounts WHERE employee_number = ?", (employee_number,)).fetchone()
        if row is None:
            return ("error", None, "対象のアカウントが見つかりません")
        borrowed = conn.execute(
            "SELECT 1 FROM lendings WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if borrowed is not None:
            return ("error", None, BORROWED_TEXT)
        if row["role"] == ROLE_MANAGER and _manager_count(conn) <= 1:
            return ("error", None, LAST_MANAGER_TEXT)
        conn.execute("DELETE FROM sessions WHERE employee_number = ?", (employee_number,))
        conn.execute("DELETE FROM accounts WHERE employee_number = ?", (employee_number,))
        ok = True
        return None
    finally:
        _finish(conn, ok)

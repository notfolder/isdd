"""アカウントの業務処理（登録、認証、一覧、担当者の付け外し、パスワード再設定、削除）。

書き込みを伴う処理は BEGIN IMMEDIATE で直列化する。担当者は 1 人以上いる状態を保つ。
"""

from werkzeug.security import check_password_hash, generate_password_hash

from .errors import RuleViolation

# 社員番号が存在しないときも同じ時間で照合するための、ダミーのハッシュ。
_DUMMY_HASH = generate_password_hash("dummy-password-for-timing")
KEEP_ONE_MANAGER_MESSAGE = "担当者が 1 人もいなくなるため、この操作はできません"
ACCOUNT_GONE_MESSAGE = "このアカウントは既に削除されています"


def register_account(conn, employee_number: str, name: str, password: str) -> bool:
    """アカウントを登録する。アカウントが 1 件も無ければ担当者、それ以外は社員。登録した役割（担当者なら True）を返す。

    社員番号が既にあれば RuleViolation（入力欄 employee_number）。
    """
    password_hash = generate_password_hash(password)
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute(
            "SELECT 1 FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone():
            raise RuleViolation("この社員番号は既に登録されています", field="employee_number")
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        is_manager = 1 if count == 0 else 0
        conn.execute(
            "INSERT INTO accounts (employee_number, name, password_hash, is_manager) VALUES (?, ?, ?, ?)",
            (employee_number, name, password_hash, is_manager),
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return bool(is_manager)


def authenticate(conn, employee_number: str, password: str) -> str | None:
    """社員番号とパスワードを照合する。合えば社員番号を返し、違えば None。

    社員番号が無い場合も同じ照合を行い、どちらが違うかを区別しないようにする。
    """
    row = conn.execute(
        "SELECT password_hash FROM accounts WHERE employee_number = ?", (employee_number,)
    ).fetchone()
    if row is None:
        check_password_hash(_DUMMY_HASH, password)
        return None
    if check_password_hash(row["password_hash"], password):
        return employee_number
    return None


def list_accounts(conn) -> list:
    """全アカウントを社員番号の昇順で返す（社員番号、名前、担当者か否か）。"""
    return conn.execute(
        "SELECT employee_number, name, is_manager FROM accounts ORDER BY employee_number"
    ).fetchall()


def set_manager_role(conn, employee_number: str, grant: bool) -> None:
    """担当者にする（grant が True）か、担当者から外す。担当者が 0 人になる操作は拒否する。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT is_manager FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if row is None:
            raise RuleViolation(ACCOUNT_GONE_MESSAGE, level="error")
        if not grant and row["is_manager"]:
            managers = conn.execute("SELECT COUNT(*) FROM accounts WHERE is_manager = 1").fetchone()[0]
            if managers <= 1:
                raise RuleViolation(KEEP_ONE_MANAGER_MESSAGE)
        conn.execute(
            "UPDATE accounts SET is_manager = ? WHERE employee_number = ?",
            (1 if grant else 0, employee_number),
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def reset_password(conn, employee_number: str, new_password: str) -> None:
    """パスワードを再設定する（ハッシュにして保存する）。アカウントが無ければ RuleViolation。"""
    password_hash = generate_password_hash(new_password)
    conn.execute("BEGIN IMMEDIATE")
    try:
        cursor = conn.execute(
            "UPDATE accounts SET password_hash = ? WHERE employee_number = ?",
            (password_hash, employee_number),
        )
        if cursor.rowcount == 0:
            raise RuleViolation(ACCOUNT_GONE_MESSAGE, level="error")
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def delete_account(conn, employee_number: str) -> None:
    """アカウントを削除する。貸出中の社員、担当者が 0 人になる削除は拒否する。

    削除前に、その社員のセッションも消す。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT is_manager FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if row is None:
            raise RuleViolation(ACCOUNT_GONE_MESSAGE, level="error")
        if conn.execute(
            "SELECT 1 FROM loans WHERE borrower_employee_number = ?", (employee_number,)
        ).fetchone():
            raise RuleViolation(
                "この社員は備品を借りているため削除できません。先に返却を処理してください"
            )
        if row["is_manager"]:
            managers = conn.execute("SELECT COUNT(*) FROM accounts WHERE is_manager = 1").fetchone()[0]
            if managers <= 1:
                raise RuleViolation(KEEP_ONE_MANAGER_MESSAGE)
        conn.execute("DELETE FROM sessions WHERE employee_number = ?", (employee_number,))
        conn.execute("DELETE FROM accounts WHERE employee_number = ?", (employee_number,))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise

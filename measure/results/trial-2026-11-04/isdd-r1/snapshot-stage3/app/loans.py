"""貸出と返却の業務処理。

備品の貸出状態は loans 表の行の有無で持つ（行が無い = 空き、行がある = 貸出中）。
返却は行を消す。履歴は残さない。版番号が一致しなければ、他の担当者の先行更新として拒否する。
"""

from .equipment import CONFLICT_MESSAGE
from .errors import RuleViolation
from .timeutil import today_jst
from .validation import validate_lent_on

BORROWER_REQUIRED_MESSAGE = "借りる社員を選んでください"
ALREADY_LENT_MESSAGE = "この備品は既に貸出中です"
ALREADY_RETURNED_MESSAGE = "この備品は既に返却されています"


def lend_equipment(conn, equipment_number: str, expected_version: int, borrower: str, lent_on: str, today: str | None = None) -> None:
    """備品を社員に貸し出す。

    借りる社員が未選択または存在しない、貸出日が不正または未来、既に貸出中、版番号の不一致は拒否する。
    """
    if today is None:
        today = today_jst()
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT version FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if row is None or row["version"] != expected_version:
            raise RuleViolation(CONFLICT_MESSAGE, level="error")
        if not borrower or conn.execute(
            "SELECT 1 FROM accounts WHERE employee_number = ?", (borrower,)
        ).fetchone() is None:
            raise RuleViolation(BORROWER_REQUIRED_MESSAGE, field="borrower")
        date_error = validate_lent_on(lent_on, today)
        if date_error:
            raise RuleViolation(date_error, field="lent_on")
        if conn.execute(
            "SELECT 1 FROM loans WHERE equipment_number = ?", (equipment_number,)
        ).fetchone():
            raise RuleViolation(ALREADY_LENT_MESSAGE)
        conn.execute(
            "INSERT INTO loans (equipment_number, borrower_employee_number, lent_on) VALUES (?, ?, ?)",
            (equipment_number, borrower, lent_on),
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def return_equipment(conn, equipment_number: str, expected_version: int) -> None:
    """備品を返却する（貸出の行を消す）。版番号が不一致なら CONFLICT、貸出中でなければ返却済みとして拒否する。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT version FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if row is None or row["version"] != expected_version:
            raise RuleViolation(CONFLICT_MESSAGE, level="error")
        cursor = conn.execute("DELETE FROM loans WHERE equipment_number = ?", (equipment_number,))
        if cursor.rowcount == 0:
            raise RuleViolation(ALREADY_RETURNED_MESSAGE)
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise

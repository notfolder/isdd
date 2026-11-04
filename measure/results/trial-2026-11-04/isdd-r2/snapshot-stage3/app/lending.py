"""貸出状況の一覧、貸出の登録、返却の登録。

備品の状態は貸出の記録の有無で決まる。返却では貸出の記録を消し、履歴は残さない。
業務エラーは (表示の種類, 入力欄の id, 文言) の組で返す。
"""

import sqlite3
from datetime import date
from typing import Optional, Tuple

from app import validation

Problem = Tuple[str, Optional[str], str]
CONFLICT_TEXT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"


def _finish(conn: sqlite3.Connection, ok: bool) -> None:
    conn.execute("COMMIT" if ok else "ROLLBACK")


def list_lending_status(conn: sqlite3.Connection) -> list:
    """全備品の貸出状況を管理番号の昇順で返す。

    Args:
        conn: DB 接続。

    Returns:
        備品の id、管理番号、備品名、版番号、借りている社員番号と名前、貸出日を持つ dict のリスト。
        貸出中でない備品は社員番号・名前・貸出日が None。
    """
    rows = conn.execute(
        "SELECT e.id, e.equipment_number, e.name, e.version, "
        "l.employee_number, a.name AS borrower_name, l.lent_on "
        "FROM equipment e "
        "LEFT JOIN lendings l ON l.equipment_id = e.id "
        "LEFT JOIN accounts a ON a.employee_number = l.employee_number "
        "ORDER BY e.equipment_number"
    ).fetchall()
    return [dict(row) for row in rows]


def lend_equipment(
    conn: sqlite3.Connection, equipment_id: int, employee_number: str, lent_on: str, today: date
) -> Optional[Problem]:
    """空きの備品を社員に貸し出して記録する。

    Args:
        conn: DB 接続。
        equipment_id: 備品の id。
        employee_number: 借りる社員の社員番号。空なら未選択として拒否する。
        lent_on: 貸出日（YYYY-MM-DD）。
        today: 今日の日付（日本時間）。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    if employee_number == "":
        return ("field", "id_borrower", "借りる社員を選んでください")
    text = validation.validate_lent_on(lent_on, today)
    if text is not None:
        return ("field", "id_lent_on", text)
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        equipment = conn.execute("SELECT 1 FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
        if equipment is None:
            return ("error", None, CONFLICT_TEXT)
        lent = conn.execute("SELECT 1 FROM lendings WHERE equipment_id = ?", (equipment_id,)).fetchone()
        if lent is not None:
            return ("message", None, "この備品は既に貸出中です")
        borrower = conn.execute(
            "SELECT 1 FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone()
        if borrower is None:
            return ("field", "id_borrower", "借りる社員を選んでください")
        conn.execute(
            "INSERT INTO lendings (equipment_id, employee_number, lent_on) VALUES (?, ?, ?)",
            (equipment_id, employee_number, lent_on),
        )
        ok = True
        return None
    except sqlite3.IntegrityError:
        return ("message", None, "この備品は既に貸出中です")
    finally:
        _finish(conn, ok)


def return_equipment(conn: sqlite3.Connection, equipment_id: int) -> Optional[Problem]:
    """貸出中の備品の返却を記録する。貸出の記録を消す。

    Args:
        conn: DB 接続。
        equipment_id: 備品の id。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        equipment = conn.execute("SELECT 1 FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
        if equipment is None:
            return ("error", None, CONFLICT_TEXT)
        cursor = conn.execute("DELETE FROM lendings WHERE equipment_id = ?", (equipment_id,))
        if cursor.rowcount == 0:
            return ("message", None, "この備品は既に返却されています")
        ok = True
        return None
    finally:
        _finish(conn, ok)

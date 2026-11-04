"""貸出の登録、返却、貸出状況の一覧、借りる社員の選択肢。"""

import sqlite3
from typing import Dict, List

RESULT_OK = "ok"
RESULT_NOT_FOUND = "not_found"
RESULT_LOANED = "loaned"
RESULT_NOT_LOANED = "not_loaned"
RESULT_NO_BORROWER = "no_borrower"


def register_loan(
    conn: sqlite3.Connection, equipment_number: str, account_id: int, lent_on: str
) -> str:
    """空きの備品に貸出を記録する。結果は RESULT_* のいずれか。

    書き込みのトランザクションを先に開き、備品・借りる社員・既存の貸出を同じ区切りで確かめる。
    同時の登録は後の登録が待ち、貸出中として扱われる。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        equipment_row = conn.execute(
            "SELECT id FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if equipment_row is None:
            conn.execute("ROLLBACK")
            return RESULT_NOT_FOUND
        borrower = conn.execute("SELECT id FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if borrower is None:
            conn.execute("ROLLBACK")
            return RESULT_NO_BORROWER
        loaned = conn.execute(
            "SELECT 1 FROM loans WHERE equipment_id = ?", (equipment_row["id"],)
        ).fetchone()
        if loaned is not None:
            conn.execute("ROLLBACK")
            return RESULT_LOANED
        conn.execute(
            "INSERT INTO loans (equipment_id, account_id, lent_on) VALUES (?, ?, ?)",
            (equipment_row["id"], account_id, lent_on),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        return RESULT_LOANED
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return RESULT_OK


def return_loan(conn: sqlite3.Connection, equipment_number: str) -> str:
    """貸出中の備品を返却する。貸出の記録は残さず消す。結果は RESULT_* のいずれか。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        equipment_row = conn.execute(
            "SELECT id FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if equipment_row is None:
            conn.execute("ROLLBACK")
            return RESULT_NOT_FOUND
        cursor = conn.execute("DELETE FROM loans WHERE equipment_id = ?", (equipment_row["id"],))
        if cursor.rowcount == 0:
            conn.execute("ROLLBACK")
            return RESULT_NOT_LOANED
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return RESULT_OK


def list_loan_status(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    """全備品を管理番号の昇順で、貸出の記録と借りている社員の名前と結んで返す。"""
    rows = conn.execute(
        """
        SELECT e.equipment_number, e.name, l.lent_on, a.name AS borrower_name
        FROM equipment e
        LEFT JOIN loans l ON l.equipment_id = e.id
        LEFT JOIN accounts a ON a.id = l.account_id
        ORDER BY e.equipment_number ASC
        """
    ).fetchall()
    return [
        {
            "equipment_number": r["equipment_number"],
            "name": r["name"],
            "loaned": r["lent_on"] is not None,
            "borrower_name": r["borrower_name"] or "",
            "lent_on": r["lent_on"] or "",
        }
        for r in rows
    ]


def list_borrowers(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    """借りる社員の選択肢を返す。表示は「名前（社員番号）」。"""
    rows = conn.execute(
        "SELECT id, name, employee_number FROM accounts ORDER BY name ASC, employee_number ASC"
    ).fetchall()
    return [
        {"id": int(r["id"]), "label": f"{r['name']}（{r['employee_number']}）"} for r in rows
    ]

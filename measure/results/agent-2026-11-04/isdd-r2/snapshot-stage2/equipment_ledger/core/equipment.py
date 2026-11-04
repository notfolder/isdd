"""備品の一覧・登録・修正・削除。"""

import sqlite3
from typing import Optional

STATUS_AVAILABLE = "空き"
STATUS_LENT = "貸出中"

DELETE_OK = "deleted"
DELETE_LENT = "lent"
DELETE_MISSING = "missing"


def list_equipment_status(conn: sqlite3.Connection) -> list[dict]:
    """管理番号の昇順に備品を返す。貸出の行があれば貸出中と借りている社員の名前・貸出日を返す。"""
    rows = conn.execute(
        """
        SELECT e.equipment_number, e.name, l.lent_on, a.name AS holder_name
        FROM equipment e
        LEFT JOIN lending l ON l.equipment_number = e.equipment_number
        LEFT JOIN account a ON a.employee_number = l.employee_number
        ORDER BY e.equipment_number ASC
        """
    ).fetchall()
    return [
        {
            "number": row["equipment_number"],
            "name": row["name"],
            "status": STATUS_LENT if row["lent_on"] is not None else STATUS_AVAILABLE,
            "holder_name": row["holder_name"] or "",
            "lent_on": row["lent_on"] or "",
        }
        for row in rows
    ]


def get_equipment(conn: sqlite3.Connection, equipment_number: str) -> Optional[dict]:
    """管理番号で 1 件を返す（備品名と版番号）。無ければ None。"""
    row = conn.execute(
        "SELECT equipment_number, name, revision FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()
    if row is None:
        return None
    return {"number": row["equipment_number"], "name": row["name"], "revision": row["revision"]}


def register_equipment(conn: sqlite3.Connection, equipment_number: str, name: str) -> bool:
    """備品を追加する。管理番号が重複したら False を返す。"""
    try:
        conn.execute(
            "INSERT INTO equipment (equipment_number, name, revision) VALUES (?, ?, 0)",
            (equipment_number, name),
        )
        return True
    except sqlite3.IntegrityError:
        return False


def update_equipment(conn: sqlite3.Connection, equipment_number: str, name: str, revision: int) -> bool:
    """開いた時点の版番号と一致するときだけ備品名を変え、版番号を 1 増やす。

    対象が無い（削除された）場合も、版番号が違う（他の担当者が変えた）場合も False を返す。
    貸出の行には触らないため、貸出は引き継がれる。
    """
    cursor = conn.execute(
        "UPDATE equipment SET name = ?, revision = revision + 1 WHERE equipment_number = ? AND revision = ?",
        (name, equipment_number, revision),
    )
    return cursor.rowcount > 0


def delete_equipment(conn: sqlite3.Connection, equipment_number: str) -> str:
    """貸出中でなければ備品を 1 件削除する。結果は DELETE_OK、DELETE_LENT、DELETE_MISSING のいずれか。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        lent = conn.execute(
            "SELECT 1 FROM lending WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if lent is not None:
            conn.execute("ROLLBACK")
            return DELETE_LENT
        cursor = conn.execute("DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,))
        conn.execute("COMMIT")
        return DELETE_OK if cursor.rowcount > 0 else DELETE_MISSING
    except Exception:
        conn.execute("ROLLBACK")
        raise

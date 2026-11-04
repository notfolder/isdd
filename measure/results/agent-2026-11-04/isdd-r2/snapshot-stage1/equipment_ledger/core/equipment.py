"""備品の一覧・登録・修正・削除。"""

import sqlite3
from typing import Optional

STATUS_AVAILABLE = "空き"


def list_equipment_status(conn: sqlite3.Connection) -> list[dict[str, str]]:
    """管理番号の昇順に備品を返す。今回の段では貸出が無いので、すべて空きとして返す。"""
    rows = conn.execute(
        "SELECT equipment_number, name FROM equipment ORDER BY equipment_number ASC"
    ).fetchall()
    return [
        {
            "number": row["equipment_number"],
            "name": row["name"],
            "status": STATUS_AVAILABLE,
            "holder_name": "",
            "lent_on": "",
        }
        for row in rows
    ]


def get_equipment(conn: sqlite3.Connection, equipment_number: str) -> Optional[dict[str, str]]:
    """管理番号で 1 件を返す。無ければ None。"""
    row = conn.execute(
        "SELECT equipment_number, name FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()
    if row is None:
        return None
    return {"number": row["equipment_number"], "name": row["name"]}


def register_equipment(conn: sqlite3.Connection, equipment_number: str, name: str) -> bool:
    """備品を追加する。管理番号が重複したら False を返す。"""
    try:
        conn.execute(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            (equipment_number, name),
        )
        return True
    except sqlite3.IntegrityError:
        return False


def update_equipment(conn: sqlite3.Connection, equipment_number: str, name: str) -> bool:
    """備品名を変える。対象が無ければ False を返す。管理番号は変えない。"""
    cursor = conn.execute(
        "UPDATE equipment SET name = ? WHERE equipment_number = ?",
        (name, equipment_number),
    )
    return cursor.rowcount > 0


def delete_equipment(conn: sqlite3.Connection, equipment_number: str) -> bool:
    """備品を 1 件削除する。記録は残さない。対象が無ければ False を返す。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        cursor = conn.execute(
            "DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,)
        )
        conn.execute("COMMIT")
        return cursor.rowcount > 0
    except Exception:
        conn.execute("ROLLBACK")
        raise

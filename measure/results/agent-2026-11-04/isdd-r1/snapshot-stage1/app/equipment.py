"""備品の一覧・取得・登録・修正・削除。"""

import sqlite3
from typing import Dict, List, Optional

from .validation import MSG_EQUIPMENT_NUMBER_DUPLICATE, validate_equipment_input


def list_equipment(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    """全備品を管理番号の昇順で返す。"""
    rows = conn.execute(
        "SELECT equipment_number, name FROM equipment ORDER BY equipment_number ASC"
    ).fetchall()
    return [{"equipment_number": r["equipment_number"], "name": r["name"]} for r in rows]


def get_equipment(conn: sqlite3.Connection, equipment_number: str) -> Optional[Dict[str, str]]:
    """管理番号で 1 件取得する。無ければ None。"""
    row = conn.execute(
        "SELECT equipment_number, name FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()
    if row is None:
        return None
    return {"equipment_number": row["equipment_number"], "name": row["name"]}


def create_equipment(conn: sqlite3.Connection, equipment_number: str, name: str) -> Dict[str, str]:
    """備品を登録する。戻り値は入力欄名から文言への辞書（空なら登録できた）。"""
    errors = validate_equipment_input(equipment_number, name)
    if errors:
        return errors
    try:
        conn.execute(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            (equipment_number, name.strip()),
        )
    except sqlite3.IntegrityError:
        return {"equipment_number": MSG_EQUIPMENT_NUMBER_DUPLICATE}
    return {}


def update_equipment(
    conn: sqlite3.Connection, current_number: str, equipment_number: str, name: str
) -> Dict[str, str]:
    """備品の管理番号と備品名を修正する。対象の存在は呼び出し側が確かめる。

    自分自身の管理番号は重複とみなさない（UNIQUE 制約は他の行とだけ衝突する）。
    """
    errors = validate_equipment_input(equipment_number, name)
    if errors:
        return errors
    try:
        conn.execute(
            "UPDATE equipment SET equipment_number = ?, name = ? WHERE equipment_number = ?",
            (equipment_number, name.strip(), current_number),
        )
    except sqlite3.IntegrityError:
        return {"equipment_number": MSG_EQUIPMENT_NUMBER_DUPLICATE}
    return {}


def delete_equipment(conn: sqlite3.Connection, equipment_number: str) -> bool:
    """備品を物理削除する。削除したら True、対象が無ければ False。履歴は残さない。"""
    cursor = conn.execute("DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,))
    return cursor.rowcount > 0

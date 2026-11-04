"""備品の取得・登録・修正・削除。"""

import sqlite3
from typing import Dict, Optional

from .validation import MSG_EQUIPMENT_NUMBER_DUPLICATE, validate_equipment_input

CONFLICT_KEY = "conflict"
MSG_EQUIPMENT_CONFLICT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"

DELETE_DELETED = "deleted"
DELETE_NOT_FOUND = "not_found"
DELETE_LOANED = "loaned"


def get_equipment_with_revision(
    conn: sqlite3.Connection, equipment_number: str
) -> Optional[Dict[str, object]]:
    """管理番号で 1 件取得し、版番号を含めて返す。無ければ None。"""
    row = conn.execute(
        "SELECT equipment_number, name, revision FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()
    if row is None:
        return None
    return {
        "equipment_number": row["equipment_number"],
        "name": row["name"],
        "revision": int(row["revision"]),
    }


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


def update_equipment_if_current(
    conn: sqlite3.Connection,
    current_number: str,
    expected_revision: Optional[int],
    equipment_number: str,
    name: str,
) -> Dict[str, str]:
    """版番号が一致するときだけ修正し、版番号を 1 増やす。貸出の記録には触れない。

    備品が無い、または版番号が違えば（他の担当者が更新・削除していた）保存せず、
    CONFLICT_KEY の文言を返す。版番号が None（画面から送られなかった）なら、備品の有無だけを見る。
    管理番号の重複は入力欄のエラーとして返す。
    """
    errors = validate_equipment_input(equipment_number, name)
    if errors:
        return errors
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT id, revision FROM equipment WHERE equipment_number = ?", (current_number,)
        ).fetchone()
        if row is None or (expected_revision is not None and int(row["revision"]) != expected_revision):
            conn.execute("ROLLBACK")
            return {CONFLICT_KEY: MSG_EQUIPMENT_CONFLICT}
        conn.execute(
            "UPDATE equipment SET equipment_number = ?, name = ?, revision = revision + 1 WHERE id = ?",
            (equipment_number, name.strip(), row["id"]),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        return {"equipment_number": MSG_EQUIPMENT_NUMBER_DUPLICATE}
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {}


def delete_equipment_if_not_loaned(conn: sqlite3.Connection, equipment_number: str) -> str:
    """貸出中でなければ物理削除する。結果は DELETE_DELETED、DELETE_NOT_FOUND、DELETE_LOANED のいずれか。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT id FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            return DELETE_NOT_FOUND
        loaned = conn.execute("SELECT 1 FROM loans WHERE equipment_id = ?", (row["id"],)).fetchone()
        if loaned is not None:
            conn.execute("ROLLBACK")
            return DELETE_LOANED
        conn.execute("DELETE FROM equipment WHERE id = ?", (row["id"],))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return DELETE_DELETED

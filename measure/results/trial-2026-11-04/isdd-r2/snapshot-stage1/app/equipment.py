"""備品の登録・修正・削除と、同時更新の検査（版番号による楽観的排他制御）。

修正と削除は、画面を開いたときの版番号と DB の版番号が一致する場合だけ行う。
業務エラーは (表示の種類, 入力欄の id, 文言) の組で返す。
"""

import sqlite3
from typing import Optional, Tuple

from app import validation

CONFLICT_TEXT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
LENT_DELETE_TEXT = "この備品は貸出中のため削除できません。先に返却を処理してください"
DUPLICATE_NUMBER_TEXT = "この管理番号は既に使われています"

Problem = Tuple[str, Optional[str], str]


def _finish(conn: sqlite3.Connection, ok: bool) -> None:
    conn.execute("COMMIT" if ok else "ROLLBACK")


def check_equipment_version(conn: sqlite3.Connection, equipment_id: int, version: int) -> bool:
    """備品が存在し、版番号が一致するかを返す。トランザクションの中で呼ぶ。

    Args:
        conn: DB 接続。
        equipment_id: 備品の id。
        version: 画面を開いたときの版番号。

    Returns:
        存在して版番号が一致すれば True。
    """
    row = conn.execute("SELECT version FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
    return row is not None and row["version"] == version


def create_equipment(conn: sqlite3.Connection, equipment_number: str, name: str) -> Optional[Problem]:
    """備品を登録する。管理番号は重複できない。

    Args:
        conn: DB 接続。
        equipment_number: 管理番号（半角の英数字とハイフン、20 文字以内）。
        name: 備品名（50 文字以内）。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    checks = [
        ("id_equipment_number", validation.validate_equipment_number(equipment_number)),
        ("id_name", validation.validate_equipment_name(name)),
    ]
    for field, text in checks:
        if text is not None:
            return ("field", field, text)
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        exists = conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if exists is not None:
            return ("field", "id_equipment_number", DUPLICATE_NUMBER_TEXT)
        conn.execute(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            (equipment_number, name.strip()),
        )
        ok = True
        return None
    except sqlite3.IntegrityError:
        return ("field", "id_equipment_number", DUPLICATE_NUMBER_TEXT)
    finally:
        _finish(conn, ok)


def update_equipment(
    conn: sqlite3.Connection, equipment_id: int, version: int, equipment_number: str, name: str
) -> Optional[Problem]:
    """備品の管理番号と備品名を修正する。版番号が古ければ拒否する。

    Args:
        conn: DB 接続。
        equipment_id: 備品の id。
        version: 画面を開いたときの版番号。
        equipment_number: 新しい管理番号。
        name: 新しい備品名。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    checks = [
        ("id_equipment_number", validation.validate_equipment_number(equipment_number)),
        ("id_name", validation.validate_equipment_name(name)),
    ]
    for field, text in checks:
        if text is not None:
            return ("field", field, text)
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        if not check_equipment_version(conn, equipment_id, version):
            return ("error", None, CONFLICT_TEXT)
        other = conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ? AND id <> ?",
            (equipment_number, equipment_id),
        ).fetchone()
        if other is not None:
            return ("field", "id_equipment_number", DUPLICATE_NUMBER_TEXT)
        conn.execute(
            "UPDATE equipment SET equipment_number = ?, name = ?, version = version + 1 WHERE id = ?",
            (equipment_number, name.strip(), equipment_id),
        )
        ok = True
        return None
    except sqlite3.IntegrityError:
        return ("field", "id_equipment_number", DUPLICATE_NUMBER_TEXT)
    finally:
        _finish(conn, ok)


def delete_equipment(conn: sqlite3.Connection, equipment_id: int, version: int) -> Optional[Problem]:
    """備品を削除する。貸出中の備品と、版番号が古い備品は拒否する。

    Args:
        conn: DB 接続。
        equipment_id: 備品の id。
        version: 画面を開いたときの版番号。

    Returns:
        成功なら None。失敗なら業務エラーの組。
    """
    conn.execute("BEGIN IMMEDIATE")
    ok = False
    try:
        if not check_equipment_version(conn, equipment_id, version):
            return ("error", None, CONFLICT_TEXT)
        lent = conn.execute("SELECT 1 FROM lendings WHERE equipment_id = ?", (equipment_id,)).fetchone()
        if lent is not None:
            return ("error", None, LENT_DELETE_TEXT)
        conn.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
        ok = True
        return None
    finally:
        _finish(conn, ok)

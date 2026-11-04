"""備品の一覧・登録・修正・削除。"""

import sqlite3

DUPLICATE_EQUIPMENT_MESSAGE = "この管理番号は既に使われています"
NOT_FOUND_MESSAGE = "対象の備品が見つかりません"
# 貸出の記録は次の段で追加する。今回は全備品が空き。
STATUS_AVAILABLE = "空き"


def list_equipment(conn):
    """全備品を管理番号の昇順で返す。各行は管理番号、備品名、状況、借りている社員、貸出日を持つ。"""
    rows = conn.execute(
        "SELECT equipment_number, name FROM equipment ORDER BY equipment_number ASC"
    ).fetchall()
    return [
        {
            "equipment_number": row["equipment_number"],
            "name": row["name"],
            "status": STATUS_AVAILABLE,
            "borrower": None,
            "lent_on": None,
        }
        for row in rows
    ]


def find_equipment(conn, equipment_number):
    """管理番号で備品を 1 件探す。無ければ None を返す。"""
    return conn.execute(
        "SELECT id, equipment_number, name FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()


def create_equipment(conn, equipment_number, name):
    """備品を登録する。管理番号が重複なら文言を返し、成功なら None を返す。"""
    try:
        conn.execute(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            (equipment_number, name),
        )
    except sqlite3.IntegrityError:
        return DUPLICATE_EQUIPMENT_MESSAGE
    return None


def update_equipment(conn, current_number, new_number, name):
    """管理番号と備品名を直す。対象が無ければ NOT_FOUND_MESSAGE、重複なら文言、成功なら None を返す。

    対象の存在の確認と更新は書き込みロック付きのトランザクションで行う。
    """
    try:
        conn.execute("BEGIN IMMEDIATE")
        if find_equipment(conn, current_number) is None:
            _rollback(conn)
            return NOT_FOUND_MESSAGE
        conn.execute(
            "UPDATE equipment SET equipment_number = ?, name = ? WHERE equipment_number = ?",
            (new_number, name, current_number),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        _rollback(conn)
        return DUPLICATE_EQUIPMENT_MESSAGE
    except BaseException:
        _rollback(conn)
        raise
    return None


def delete_equipment(conn, equipment_number):
    """備品を削除する。削除の記録は残さない。削除したら True、対象が無ければ False を返す。"""
    cursor = conn.execute("DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,))
    return cursor.rowcount == 1


def _rollback(conn):
    if conn.in_transaction:
        conn.execute("ROLLBACK")

"""備品の貸出と返却。貸出の記録は備品の内部 ID に結びつけ、書き込みロックの中で確かめてから変える。

戻り値の文言は画面の `.message` か、借りる社員の `.field-error` に出す。
"""

import sqlite3

from equipment_ledger.equipment import NOT_FOUND_MESSAGE

ALREADY_LENT_MESSAGE = "この備品は既に貸出中です"
ALREADY_RETURNED_MESSAGE = "この備品は既に返却されています"
BORROWER_MISSING_MESSAGE = "借りる社員を選んでください"


def is_lent(conn, equipment_number):
    """備品が貸出中（貸出の行がある）かを返す。対象の備品が無ければ False。"""
    return (
        conn.execute(
            "SELECT 1 FROM loans AS l JOIN equipment AS e ON e.id = l.equipment_id "
            "WHERE e.equipment_number = ?",
            (equipment_number,),
        ).fetchone()
        is not None
    )


def lend_equipment(conn, equipment_number, borrower_id, lent_on):
    """備品を借りる社員に貸し出す。貸出の行を 1 件挿入する。

    戻り値: 成功なら None。備品が無ければ NOT_FOUND_MESSAGE、借りる社員が無ければ
    BORROWER_MISSING_MESSAGE、既に貸出中（先の登録が入っていた場合を含む）なら ALREADY_LENT_MESSAGE。
    """
    try:
        conn.execute("BEGIN IMMEDIATE")
        equipment = conn.execute(
            "SELECT id FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if equipment is None:
            _rollback(conn)
            return NOT_FOUND_MESSAGE
        borrower = conn.execute("SELECT id FROM accounts WHERE id = ?", (borrower_id,)).fetchone()
        if borrower is None:
            _rollback(conn)
            return BORROWER_MISSING_MESSAGE
        lent = conn.execute(
            "SELECT 1 FROM loans WHERE equipment_id = ?", (equipment["id"],)
        ).fetchone()
        if lent is not None:
            _rollback(conn)
            return ALREADY_LENT_MESSAGE
        conn.execute(
            "INSERT INTO loans (equipment_id, borrower_id, lent_on) VALUES (?, ?, ?)",
            (equipment["id"], borrower["id"], lent_on),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        _rollback(conn)
        return ALREADY_LENT_MESSAGE
    except BaseException:
        _rollback(conn)
        raise
    return None


def return_equipment(conn, equipment_number):
    """備品の返却を処理する。貸出の行を消す（返却の記録は残さない）。

    戻り値: 成功なら None。備品が無ければ NOT_FOUND_MESSAGE、貸出の行が無ければ（既に返却済み）
    ALREADY_RETURNED_MESSAGE。確かめと削除は書き込みロック付きのトランザクションで行う。
    """
    try:
        conn.execute("BEGIN IMMEDIATE")
        equipment = conn.execute(
            "SELECT id FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if equipment is None:
            _rollback(conn)
            return NOT_FOUND_MESSAGE
        cursor = conn.execute("DELETE FROM loans WHERE equipment_id = ?", (equipment["id"],))
        if cursor.rowcount != 1:
            _rollback(conn)
            return ALREADY_RETURNED_MESSAGE
        conn.execute("COMMIT")
    except BaseException:
        _rollback(conn)
        raise
    return None


def _rollback(conn):
    if conn.in_transaction:
        conn.execute("ROLLBACK")

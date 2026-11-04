"""備品の一覧・登録・修正・削除。"""

import sqlite3

DUPLICATE_EQUIPMENT_MESSAGE = "この管理番号は既に使われています"
NOT_FOUND_MESSAGE = "対象の備品が見つかりません"
CONFLICT_MESSAGE = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
LENT_DELETE_MESSAGE = "この備品は貸出中のため削除できません。先に返却を処理してください"
STATUS_AVAILABLE = "空き"
STATUS_LENT = "貸出中"


def list_equipment(conn):
    """全備品を管理番号の昇順で返す。各行は管理番号、備品名、状況、借りている社員、貸出日を持つ。

    貸出の行が無い備品は「空き」で、借りている社員と貸出日は None。
    """
    rows = conn.execute(
        """
        SELECT e.equipment_number, e.name, a.name AS borrower, l.lent_on
        FROM equipment AS e
        LEFT JOIN loans AS l ON l.equipment_id = e.id
        LEFT JOIN accounts AS a ON a.id = l.borrower_id
        ORDER BY e.equipment_number ASC
        """
    ).fetchall()
    return [
        {
            "equipment_number": row["equipment_number"],
            "name": row["name"],
            "status": STATUS_LENT if row["borrower"] is not None else STATUS_AVAILABLE,
            "borrower": row["borrower"],
            "lent_on": row["lent_on"],
        }
        for row in rows
    ]


def find_equipment(conn, equipment_number):
    """管理番号で備品を 1 件探す。無ければ None を返す。行は版番号を含む。"""
    return conn.execute(
        "SELECT id, equipment_number, name, revision FROM equipment WHERE equipment_number = ?",
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


def update_equipment(conn, current_number, revision, new_number, name):
    """管理番号と備品名を直す。版番号が開いたときと一致する行だけを更新し、版番号を 1 増やす。

    戻り値: 成功なら None。他の担当者が先に更新・削除していれば CONFLICT_MESSAGE（版番号が一致しない、
    版番号が整数でない、対象が無い場合を含む）。管理番号が他の備品と重なれば DUPLICATE_EQUIPMENT_MESSAGE。
    1 文の UPDATE なので、確かめと更新は同時に行われる。
    """
    try:
        expected_revision = int(revision)
    except (TypeError, ValueError):
        return CONFLICT_MESSAGE
    try:
        cursor = conn.execute(
            "UPDATE equipment SET equipment_number = ?, name = ?, revision = revision + 1 "
            "WHERE equipment_number = ? AND revision = ?",
            (new_number, name, current_number, expected_revision),
        )
    except sqlite3.IntegrityError:
        return DUPLICATE_EQUIPMENT_MESSAGE
    return None if cursor.rowcount == 1 else CONFLICT_MESSAGE


def delete_equipment(conn, equipment_number):
    """備品を削除する。貸出中の備品は削除しない。削除の記録は残さない。

    戻り値: 成功なら None。対象が無ければ NOT_FOUND_MESSAGE、貸出中なら LENT_DELETE_MESSAGE。
    貸出の確かめと削除は書き込みロック付きのトランザクションで行う。
    """
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if row is None:
            _rollback(conn)
            return NOT_FOUND_MESSAGE
        lent = conn.execute("SELECT 1 FROM loans WHERE equipment_id = ?", (row["id"],)).fetchone()
        if lent is not None:
            _rollback(conn)
            return LENT_DELETE_MESSAGE
        conn.execute("DELETE FROM equipment WHERE id = ?", (row["id"],))
        conn.execute("COMMIT")
    except BaseException:
        _rollback(conn)
        raise
    return None


def _rollback(conn):
    if conn.in_transaction:
        conn.execute("ROLLBACK")

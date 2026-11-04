"""備品の一覧・取得・登録・修正・削除。書き込みは BEGIN IMMEDIATE の 1 つのトランザクションで行う。"""

from datetime import datetime, timezone

MSG_EQUIPMENT_NUMBER_DUPLICATE = "この管理番号は既に使われています"
STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"
STATUS_INVALID = "invalid"


def _now_text():
    """現在時刻を ISO 8601 の文字列（UTC）で返す。"""
    return datetime.now(timezone.utc).isoformat()


def list_equipment(conn):
    """全備品を管理番号の昇順で返す。

    戻り値は管理番号（equipment_number）と備品名（name）を持つ辞書のリスト。
    """
    rows = conn.execute(
        "SELECT equipment_number, name FROM equipment ORDER BY equipment_number"
    ).fetchall()
    return [{"equipment_number": row["equipment_number"], "name": row["name"]} for row in rows]


def get_equipment(conn, equipment_number):
    """管理番号の備品を返す。無ければ None。戻り値は管理番号と備品名を持つ辞書。"""
    row = conn.execute(
        "SELECT equipment_number, name FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()
    if row is None:
        return None
    return {"equipment_number": row["equipment_number"], "name": row["name"]}


def create_equipment(conn, equipment_number, name):
    """備品を登録する。

    戻り値は (エラーの辞書, 状態)。管理番号が既にあれば、項目 equipment_number に
    文言を入れたエラーの辞書を返し、登録しない。成功時はエラーの辞書が空。
    """
    now = _now_text()
    conn.execute("BEGIN IMMEDIATE")
    try:
        exists = conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if exists is not None:
            conn.execute("ROLLBACK")
            return {"equipment_number": MSG_EQUIPMENT_NUMBER_DUPLICATE}, STATUS_INVALID
        conn.execute(
            "INSERT INTO equipment (equipment_number, name, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (equipment_number, name, now, now),
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {}, STATUS_OK


def update_equipment(conn, old_number, new_number, name):
    """備品の管理番号と備品名を修正する。

    戻り値は (エラーの辞書, 状態)。対象が無ければ状態 STATUS_NOT_FOUND。
    管理番号を別の番号に変える場合、その番号が既にあればエラーの辞書を返して変更しない。
    自分自身の番号への保存は重複として扱わない。
    """
    now = _now_text()
    conn.execute("BEGIN IMMEDIATE")
    try:
        current = conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (old_number,)
        ).fetchone()
        if current is None:
            conn.execute("ROLLBACK")
            return {}, STATUS_NOT_FOUND
        if new_number != old_number:
            taken = conn.execute(
                "SELECT 1 FROM equipment WHERE equipment_number = ?", (new_number,)
            ).fetchone()
            if taken is not None:
                conn.execute("ROLLBACK")
                return {"equipment_number": MSG_EQUIPMENT_NUMBER_DUPLICATE}, STATUS_INVALID
        conn.execute(
            "UPDATE equipment SET equipment_number = ?, name = ?, updated_at = ? "
            "WHERE equipment_number = ?",
            (new_number, name, now, old_number),
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {}, STATUS_OK


def delete_equipment(conn, equipment_number):
    """備品を削除する。削除の記録は残さない。

    戻り値は (状態)。対象が無ければ STATUS_NOT_FOUND、削除できたら STATUS_OK。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        cursor = conn.execute(
            "DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,)
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return STATUS_OK if cursor.rowcount == 1 else STATUS_NOT_FOUND

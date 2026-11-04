"""備品の一覧・取得・登録・修正・削除。書き込みは BEGIN IMMEDIATE の 1 つのトランザクションで行う。"""

from datetime import datetime, timezone

MSG_EQUIPMENT_NUMBER_DUPLICATE = "この管理番号は既に使われています"
STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"
STATUS_INVALID = "invalid"
STATUS_CONFLICT = "conflict"
STATUS_LENT = "lent"


def _now_text():
    """現在時刻を ISO 8601 の文字列（UTC）で返す。備品の更新時刻（修正の競合の検知に使う）に使う。"""
    return datetime.now(timezone.utc).isoformat()


def list_equipment(conn):
    """全備品を管理番号の昇順で返す。貸出中の備品は借りている社員の名前と貸出日を持つ。

    戻り値は管理番号（equipment_number）、備品名（name）、貸出中か（lent）、
    借りている社員の名前（borrower_name。空き・無しは None）、貸出日（lent_on。無しは None）を持つ辞書のリスト。
    """
    rows = conn.execute(
        "SELECT e.equipment_number, e.name, l.lent_on, a.name AS borrower_name "
        "FROM equipment e "
        "LEFT JOIN lendings l ON l.equipment_number = e.equipment_number "
        "LEFT JOIN accounts a ON a.employee_number = l.employee_number "
        "ORDER BY e.equipment_number"
    ).fetchall()
    return [
        {
            "equipment_number": row["equipment_number"],
            "name": row["name"],
            "lent": row["lent_on"] is not None,
            "borrower_name": row["borrower_name"],
            "lent_on": row["lent_on"],
        }
        for row in rows
    ]


def get_equipment(conn, equipment_number):
    """管理番号の備品を返す。無ければ None。

    戻り値は管理番号（equipment_number）、備品名（name）、更新時刻（updated_at）を持つ辞書。
    更新時刻は修正の画面に隠し項目として渡し、保存時に他の担当者の更新を検知するために使う。
    """
    row = conn.execute(
        "SELECT equipment_number, name, updated_at FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()
    if row is None:
        return None
    return {
        "equipment_number": row["equipment_number"],
        "name": row["name"],
        "updated_at": row["updated_at"],
    }


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


def update_equipment(conn, old_number, new_number, name, loaded_updated_at):
    """備品の管理番号と備品名を修正する。

    引数 loaded_updated_at は修正の画面を開いたときの更新時刻。保存時点の更新時刻と違う、
    または備品が無ければ（他の担当者が先に更新・削除した）、保存せず状態 STATUS_CONFLICT を返す。
    管理番号を別の番号に変える場合、その番号が既にあればエラーの辞書を返して変更しない。
    自分自身の番号への保存は重複として扱わない。貸出の行は外部キーの連動更新で同じ備品に付いたままになる。
    戻り値は (エラーの辞書, 状態)。
    """
    now = _now_text()
    conn.execute("BEGIN IMMEDIATE")
    try:
        current = conn.execute(
            "SELECT updated_at FROM equipment WHERE equipment_number = ?", (old_number,)
        ).fetchone()
        if current is None or current["updated_at"] != loaded_updated_at:
            conn.execute("ROLLBACK")
            return {}, STATUS_CONFLICT
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
    """備品を削除する。削除の記録は残さない。貸出中の備品は削除しない。

    戻り値は状態。対象が無ければ STATUS_NOT_FOUND、貸出中なら STATUS_LENT（削除しない）、
    削除できたら STATUS_OK。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone() is None:
            conn.execute("ROLLBACK")
            return STATUS_NOT_FOUND
        if conn.execute(
            "SELECT 1 FROM lendings WHERE equipment_number = ?", (equipment_number,)
        ).fetchone() is not None:
            conn.execute("ROLLBACK")
            return STATUS_LENT
        conn.execute("DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return STATUS_OK

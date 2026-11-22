"""SQL の文字列と実行。判定はここに書かず rules.py に任せる。"""

from app.core.db import get_db

# 物ごとの現在の状態。state は貸出の行を読むときに CASE 式で作る（期限を過ぎたら overdue）。
_ITEM_SELECT = """
SELECT i.code, i.name,
       l.employee_no AS borrower, l.lent_on, l.due_on,
       CASE WHEN l.id IS NULL THEN 'free'
            WHEN :today > l.due_on THEN 'overdue'
            ELSE 'lent' END AS state
FROM whiteboards_items i
LEFT JOIN whiteboards_loans l ON l.item_code = i.code AND l.returned_on IS NULL
"""


def list_items(today: str, q: str = ""):
    """物の一覧（番号の昇順）。q があれば番号か名前の一部で絞り込む。"""
    sql = _ITEM_SELECT
    params = {"today": today}
    if q:
        sql += " WHERE i.code LIKE :q ESCAPE '\\' OR i.name LIKE :q ESCAPE '\\'"
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params["q"] = f"%{escaped}%"
    return get_db().execute(sql + " ORDER BY i.code", params).fetchall()


def get_item(code: str, today: str):
    return get_db().execute(_ITEM_SELECT + " WHERE i.code = :code", {"today": today, "code": code}).fetchone()


def insert_item(code: str, name: str) -> None:
    get_db().execute("INSERT INTO whiteboards_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code: str, name: str) -> None:
    get_db().execute("UPDATE whiteboards_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code: str) -> None:
    get_db().execute("DELETE FROM whiteboards_items WHERE code = ?", (code,))


def get_active_employee(employee_no: str):
    """在籍している社員だけを返す。退職者と存在しない番号は None。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status = 'active'",
        (employee_no,),
    ).fetchone()


def count_loans(employee_no: str, today: str):
    """社員が今借りている件数と、そのうち期限を過ぎた件数。"""
    row = get_db().execute(
        """
        SELECT COUNT(*) AS active,
               COALESCE(SUM(CASE WHEN :today > due_on THEN 1 ELSE 0 END), 0) AS overdue
        FROM whiteboards_loans WHERE employee_no = :no AND returned_on IS NULL
        """,
        {"today": today, "no": employee_no},
    ).fetchone()
    return row["active"], row["overdue"]


def insert_loan(item_code: str, employee_no: str, lent_on: str, due_on: str) -> None:
    get_db().execute(
        "INSERT INTO whiteboards_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item_code, employee_no, lent_on, due_on),
    )


def close_loan(item_code: str, returned_on: str) -> None:
    get_db().execute(
        "UPDATE whiteboards_loans SET returned_on = ? WHERE item_code = ? AND returned_on IS NULL",
        (returned_on, item_code),
    )


def list_history():
    """返却済みの貸出（新しい順）。"""
    return get_db().execute(
        """
        SELECT l.id, l.item_code, i.name AS item_name, l.employee_no, l.lent_on, l.due_on, l.returned_on
        FROM whiteboards_loans l LEFT JOIN whiteboards_items i ON i.code = l.item_code
        WHERE l.returned_on IS NOT NULL
        ORDER BY l.returned_on DESC, l.id DESC
        """
    ).fetchall()

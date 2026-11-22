"""ノート PC の貸出の SQL。判定はしない。"""

from app.core.db import get_db


def list_items(q=""):
    """物の一覧（借りている社員と貸出日・期限つき）。q があれば番号か名前の一部で絞り込む。"""
    like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    return get_db().execute(
        """
        SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on
        FROM laptops_items i
        LEFT JOIN laptops_loans l ON l.item_code = i.code AND l.returned_on IS NULL
        WHERE i.code LIKE ? ESCAPE '\\' OR i.name LIKE ? ESCAPE '\\'
        ORDER BY i.code
        """,
        (like, like),
    ).fetchall()


def get_item(code):
    return get_db().execute("SELECT code, name FROM laptops_items WHERE code = ?", (code,)).fetchone()


def insert_item(code, name):
    get_db().execute("INSERT INTO laptops_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code, name):
    get_db().execute("UPDATE laptops_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM laptops_items WHERE code = ?", (code,))


def get_active_loan(item_code):
    """返却されていない貸出。無ければ None。"""
    return get_db().execute(
        "SELECT * FROM laptops_loans WHERE item_code = ? AND returned_on IS NULL", (item_code,)
    ).fetchone()


def get_borrowable_employee(employee_no):
    """在籍している社員だけを返す。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'",
        (employee_no,),
    ).fetchone()


def count_active_loans(employee_no):
    return get_db().execute(
        "SELECT COUNT(*) FROM laptops_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchone()[0]


def count_loans_past_due(employee_no, today_text):
    """返却の期限を過ぎた（今日 > 期限）貸出の数。"""
    return get_db().execute(
        "SELECT COUNT(*) FROM laptops_loans WHERE employee_no = ? AND returned_on IS NULL AND due_on < ?",
        (employee_no, today_text),
    ).fetchone()[0]


def insert_loan(item, employee_no, lent_on, due_on):
    get_db().execute(
        "INSERT INTO laptops_loans (item_code, item_name, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?, ?)",
        (item["code"], item["name"], employee_no, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE laptops_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))


def list_history():
    return get_db().execute(
        """
        SELECT l.item_code, l.item_name, l.employee_no, e.name AS employee_name, l.lent_on, l.due_on, l.returned_on
        FROM laptops_loans l LEFT JOIN employees e ON e.employee_no = l.employee_no
        WHERE l.returned_on IS NOT NULL
        ORDER BY l.returned_on DESC, l.id DESC
        """
    ).fetchall()


def list_status(today_text):
    """status.json 用。状態は SQL の条件で決める（期限が今日より前なら期限切れの状態値を返す）。"""
    return get_db().execute(
        """
        SELECT i.code, i.name,
               CASE WHEN l.id IS NULL THEN 'free' WHEN l.due_on < ? THEN 'overdue' ELSE 'lent' END AS status,
               l.employee_no AS borrower, l.lent_on, l.due_on
        FROM laptops_items i
        LEFT JOIN laptops_loans l ON l.item_code = i.code AND l.returned_on IS NULL
        ORDER BY i.code
        """,
        (today_text,),
    ).fetchall()

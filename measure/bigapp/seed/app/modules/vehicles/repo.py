"""社用車の貸出のデータ操作（SQL はここだけに置く）。commit は呼び出し側で行う。"""

from app.core.db import get_db


def list_items(keyword=""):
    """物の一覧。貸出中なら借りている社員と貸出日・期限を付ける。番号の昇順。"""
    sql = (
        "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on "
        "FROM vehicles_items i LEFT JOIN vehicles_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
    )
    params = []
    if keyword:
        sql += "WHERE i.code LIKE ? OR i.name LIKE ? "
        like = f"%{keyword}%"
        params += [like, like]
    return get_db().execute(sql + "ORDER BY i.code", params).fetchall()


def find_item(code):
    return get_db().execute("SELECT * FROM vehicles_items WHERE code = ?", (code,)).fetchone()


def insert_item(code, name):
    get_db().execute("INSERT INTO vehicles_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code, name):
    get_db().execute("UPDATE vehicles_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM vehicles_items WHERE code = ?", (code,))


def find_open_loan(item_code):
    """返却されていない貸出（貸出中の記録）。"""
    return get_db().execute(
        "SELECT * FROM vehicles_loans WHERE item_code = ? AND returned_on IS NULL", (item_code,)
    ).fetchone()


def count_open_loans(employee_no):
    """その社員が今借りている件数。"""
    return get_db().execute(
        "SELECT COUNT(*) FROM vehicles_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchone()[0]


def count_past_due_loans(employee_no, today_text):
    """返却の期限を過ぎたまま持っている貸出の件数。"""
    return get_db().execute(
        "SELECT COUNT(*) FROM vehicles_loans WHERE employee_no = ? AND returned_on IS NULL AND due_on < ?",
        (employee_no, today_text),
    ).fetchone()[0]


def find_employee(employee_no):
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()


def find_active_employee(employee_no):
    """在籍している（退職していない）社員。"""
    return get_db().execute(
        "SELECT * FROM employees WHERE employee_no = ? AND status != 'retired'", (employee_no,)
    ).fetchone()


def insert_loan(item_code, employee_no, lent_on, due_on):
    get_db().execute(
        "INSERT INTO vehicles_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item_code, employee_no, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE vehicles_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))


def list_history():
    """返却済みの貸出。新しい順。"""
    return get_db().execute(
        "SELECT l.*, i.name AS item_name, e.name AS employee_name FROM vehicles_loans l "
        "LEFT JOIN vehicles_items i ON i.code = l.item_code "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()


def list_status(today_text):
    """状態の一覧。期限を過ぎている貸出は SQL の条件（due_on < ?）で見分ける。"""
    return get_db().execute(
        "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, "
        "CASE WHEN l.id IS NULL THEN 'free' WHEN l.due_on < ? THEN 'overdue' ELSE 'lent' END AS status "
        "FROM vehicles_items i LEFT JOIN vehicles_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
        "ORDER BY i.code",
        (today_text,),
    ).fetchall()

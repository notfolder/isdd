"""制服の貸与の SQL。判定は service.py で行い、ここは読み書きだけをする。"""

from app.core.db import get_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS uniforms_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS uniforms_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""


def find_item(code):
    return get_db().execute("SELECT * FROM uniforms_items WHERE code = ?", (code,)).fetchone()


def insert_item(code, name):
    get_db().execute("INSERT INTO uniforms_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code, name):
    get_db().execute("UPDATE uniforms_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM uniforms_items WHERE code = ?", (code,))


def find_employee(employee_no):
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()


def open_loan_for_item(code):
    """返却されていない貸出（物ごとに高々 1 件）。"""
    return get_db().execute(
        "SELECT * FROM uniforms_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def open_loans_of_employee(employee_no):
    return get_db().execute(
        "SELECT * FROM uniforms_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchall()


def insert_loan(code, employee_no, lent_on, due_on):
    get_db().execute(
        "INSERT INTO uniforms_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, employee_no, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE uniforms_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))


def list_items_with_loans(query=""):
    """物の一覧。貸出中なら借りている社員と日付も付ける。番号の昇順。"""
    sql = (
        "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, e.name AS borrower_name "
        "FROM uniforms_items i "
        "LEFT JOIN uniforms_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
    )
    params = []
    if query:
        sql += "WHERE i.code LIKE ? OR i.name LIKE ? "
        like = f"%{query}%"
        params = [like, like]
    sql += "ORDER BY i.code"
    return get_db().execute(sql, params).fetchall()


def list_history():
    """返却済みの貸出。新しい順。"""
    return get_db().execute(
        "SELECT l.*, i.name AS item_name, e.name AS borrower_name FROM uniforms_loans l "
        "LEFT JOIN uniforms_items i ON i.code = l.item_code "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()

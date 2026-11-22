"""駐車許可証の貸出の SQL。判定は service.py に置き、ここは読み書きだけを行う。"""

from app.core.db import get_db


def find_item(code):
    return get_db().execute("SELECT code, name FROM parking_passes_items WHERE code = ?", (code,)).fetchone()


def insert_item(code, name):
    get_db().execute("INSERT INTO parking_passes_items (code, name) VALUES (?, ?)", (code, name))


def update_item_name(code, name):
    get_db().execute("UPDATE parking_passes_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM parking_passes_items WHERE code = ?", (code,))


def find_active_employee(employee_no):
    """在籍している社員だけを読む。退職者と存在しない番号は None。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'",
        (employee_no,),
    ).fetchone()


def open_loan_of_item(code):
    """物の貸出中の記録（返却前のもの）。"""
    return get_db().execute(
        "SELECT * FROM parking_passes_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def open_loans_of_employee(employee_no):
    return get_db().execute(
        "SELECT * FROM parking_passes_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchall()


def insert_loan(item, employee_no, lent_on, due_on):
    get_db().execute(
        "INSERT INTO parking_passes_loans (item_code, item_name, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?, ?)",
        (item["code"], item["name"], employee_no, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE parking_passes_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))


def list_items(q=""):
    """物の一覧（貸出中なら借りている社員と期限つき）。番号の昇順。q は番号か名前の一部。"""
    like = f"%{q}%"
    return get_db().execute(
        """
        SELECT i.code, i.name, l.employee_no AS borrower, e.name AS borrower_name, l.lent_on, l.due_on
        FROM parking_passes_items i
        LEFT JOIN parking_passes_loans l ON l.item_code = i.code AND l.returned_on IS NULL
        LEFT JOIN employees e ON e.employee_no = l.employee_no
        WHERE i.code LIKE ? OR i.name LIKE ?
        ORDER BY i.code
        """,
        (like, like),
    ).fetchall()


def list_history():
    return get_db().execute(
        """
        SELECT l.id, l.item_code, l.item_name, l.employee_no, e.name AS employee_name, l.lent_on, l.due_on, l.returned_on
        FROM parking_passes_loans l LEFT JOIN employees e ON e.employee_no = l.employee_no
        WHERE l.returned_on IS NOT NULL
        ORDER BY l.returned_on DESC, l.id DESC
        """
    ).fetchall()

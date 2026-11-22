"""社用自転車の SQL。"""

from app.core.db import get_db

SELECT_ITEMS = """
SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, e.name AS borrower_name
FROM bicycles_items i
LEFT JOIN bicycles_loans l ON l.item_code = i.code AND l.returned_on IS NULL
LEFT JOIN employees e ON e.employee_no = l.employee_no
WHERE i.code LIKE ? ESCAPE '\\' OR i.name LIKE ? ESCAPE '\\'
ORDER BY i.code
"""

SELECT_HISTORY = """
SELECT l.id, l.item_code, i.name AS item_name, l.employee_no, e.name AS employee_name, l.lent_on, l.due_on, l.returned_on
FROM bicycles_loans l
LEFT JOIN bicycles_items i ON i.code = l.item_code
LEFT JOIN employees e ON e.employee_no = l.employee_no
WHERE l.returned_on IS NOT NULL
ORDER BY l.returned_on DESC, l.id DESC
"""


def list_items(q: str = ""):
    """番号か名前に q を含む物を、貸出の状況つきで番号順に返す。"""
    like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    return get_db().execute(SELECT_ITEMS, (like, like)).fetchall()


def get_item(code):
    return get_db().execute("SELECT * FROM bicycles_items WHERE code = ?", (code,)).fetchone()


def insert_item(code, name):
    get_db().execute("INSERT INTO bicycles_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code, name):
    get_db().execute("UPDATE bicycles_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM bicycles_items WHERE code = ?", (code,))


def open_loan_of_item(code):
    """物の貸出中の記録。貸出中でなければ None。"""
    return get_db().execute("SELECT * FROM bicycles_loans WHERE item_code = ? AND returned_on IS NULL", (code,)).fetchone()


def open_loan_of_employee(employee_no):
    """社員がこの機能で持っている貸出中の記録。無ければ None。"""
    return get_db().execute("SELECT * FROM bicycles_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)).fetchone()


def get_employee(employee_no):
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()


def insert_loan(code, employee_no, lent_on, due_on):
    get_db().execute(
        "INSERT INTO bicycles_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, employee_no, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE bicycles_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))


def list_history():
    return get_db().execute(SELECT_HISTORY).fetchall()

"""SQL とその実行。"""

from app.core.db import get_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS monitors_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitors_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

SELECT_ITEM = "SELECT code, name FROM monitors_items WHERE code = ?"
SELECT_ACTIVE_EMPLOYEE = "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status = 'active'"
SELECT_OPEN_LOAN = "SELECT * FROM monitors_loans WHERE item_code = ? AND returned_on IS NULL"
SELECT_OPEN_LOANS_OF = "SELECT * FROM monitors_loans WHERE employee_no = ? AND returned_on IS NULL"
SELECT_LIST = """
SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on
FROM monitors_items i
LEFT JOIN monitors_loans l ON l.item_code = i.code AND l.returned_on IS NULL
WHERE (? = '' OR i.code LIKE '%' || ? || '%' OR i.name LIKE '%' || ? || '%')
ORDER BY i.code
"""
SELECT_HISTORY = """
SELECT l.item_code, i.name, l.employee_no, l.lent_on, l.due_on, l.returned_on
FROM monitors_loans l
LEFT JOIN monitors_items i ON i.code = l.item_code
WHERE l.returned_on IS NOT NULL
ORDER BY l.returned_on DESC, l.id DESC
"""


def get_item(code):
    return get_db().execute(SELECT_ITEM, (code,)).fetchone()


def get_active_employee(number):
    return get_db().execute(SELECT_ACTIVE_EMPLOYEE, (number,)).fetchone()


def get_open_loan(code):
    return get_db().execute(SELECT_OPEN_LOAN, (code,)).fetchone()


def get_open_loans_of(number):
    return get_db().execute(SELECT_OPEN_LOANS_OF, (number,)).fetchall()


def list_items(q=""):
    return get_db().execute(SELECT_LIST, (q, q, q)).fetchall()


def list_history():
    return get_db().execute(SELECT_HISTORY).fetchall()


def insert_item(code, name):
    get_db().execute("INSERT INTO monitors_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code, name):
    get_db().execute("UPDATE monitors_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM monitors_items WHERE code = ?", (code,))


def insert_loan(code, number, lent_on, due_on):
    get_db().execute(
        "INSERT INTO monitors_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, number, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE monitors_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))

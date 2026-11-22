"""SQL の文字列と実行。"""

from app.core.db import get_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS tools_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tools_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

SQL_ITEMS = """
SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on
FROM tools_items i
LEFT JOIN tools_loans l ON l.item_code = i.code AND l.returned_on IS NULL
WHERE i.code LIKE ? ESCAPE '\\' OR i.name LIKE ? ESCAPE '\\'
ORDER BY i.code
"""
SQL_HISTORY = """
SELECT l.item_code, i.name, l.employee_no, l.lent_on, l.due_on, l.returned_on
FROM tools_loans l LEFT JOIN tools_items i ON i.code = l.item_code
WHERE l.returned_on IS NOT NULL
ORDER BY l.returned_on DESC, l.id DESC
"""


def _like(text):
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def list_items(q=""):
    pattern = _like(q)
    return get_db().execute(SQL_ITEMS, (pattern, pattern)).fetchall()


def list_history():
    return get_db().execute(SQL_HISTORY).fetchall()


def get_item(code):
    return get_db().execute("SELECT * FROM tools_items WHERE code = ?", (code,)).fetchone()


def insert_item(code, name):
    get_db().execute("INSERT INTO tools_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code, name):
    get_db().execute("UPDATE tools_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM tools_items WHERE code = ?", (code,))


def get_employee(employee_no):
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()


def get_open_loan(item_code):
    return get_db().execute("SELECT * FROM tools_loans WHERE item_code = ? AND returned_on IS NULL", (item_code,)).fetchone()


def list_open_loans_of(employee_no):
    return get_db().execute("SELECT * FROM tools_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)).fetchall()


def insert_loan(item_code, employee_no, lent_on, due_on):
    get_db().execute(
        "INSERT INTO tools_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item_code, employee_no, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE tools_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))

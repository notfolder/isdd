"""SQL の文字列と実行。判定はここに書かない。"""

from app.core.db import get_db

SELECT_ACTIVE_EMPLOYEE = "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status = 'active'"
SELECT_ITEM = "SELECT code, name FROM first_aid_kits_items WHERE code = ?"
SELECT_ITEMS = "SELECT code, name FROM first_aid_kits_items WHERE code LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' ORDER BY code"
INSERT_ITEM = "INSERT INTO first_aid_kits_items (code, name) VALUES (?, ?)"
UPDATE_ITEM = "UPDATE first_aid_kits_items SET name = ? WHERE code = ?"
DELETE_ITEM = "DELETE FROM first_aid_kits_items WHERE code = ?"
SELECT_OPEN_LOAN = "SELECT * FROM first_aid_kits_loans WHERE item_code = ? AND returned_on IS NULL"
SELECT_OPEN_LOANS_OF = "SELECT * FROM first_aid_kits_loans WHERE employee_no = ? AND returned_on IS NULL"
SELECT_OPEN_LOANS = "SELECT * FROM first_aid_kits_loans WHERE returned_on IS NULL"
INSERT_LOAN = "INSERT INTO first_aid_kits_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)"
CLOSE_LOAN = "UPDATE first_aid_kits_loans SET returned_on = ? WHERE id = ?"
SELECT_HISTORY = (
    "SELECT l.*, i.name AS item_name FROM first_aid_kits_loans l "
    "LEFT JOIN first_aid_kits_items i ON i.code = l.item_code "
    "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
)


def _like(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def find_active_employee(employee_no):
    return get_db().execute(SELECT_ACTIVE_EMPLOYEE, (employee_no,)).fetchone()


def find_item(code):
    return get_db().execute(SELECT_ITEM, (code,)).fetchone()


def list_items(q=""):
    return get_db().execute(SELECT_ITEMS, (_like(q), _like(q))).fetchall()


def insert_item(code, name):
    get_db().execute(INSERT_ITEM, (code, name))


def update_item(code, name):
    get_db().execute(UPDATE_ITEM, (name, code))


def delete_item(code):
    get_db().execute(DELETE_ITEM, (code,))


def open_loan_of_item(code):
    return get_db().execute(SELECT_OPEN_LOAN, (code,)).fetchone()


def open_loans_of_employee(employee_no):
    return get_db().execute(SELECT_OPEN_LOANS_OF, (employee_no,)).fetchall()


def open_loans_by_item():
    return {r["item_code"]: r for r in get_db().execute(SELECT_OPEN_LOANS).fetchall()}


def insert_loan(item_code, employee_no, lent_on, due_on):
    get_db().execute(INSERT_LOAN, (item_code, employee_no, lent_on, due_on))


def close_loan(loan_id, returned_on):
    get_db().execute(CLOSE_LOAN, (returned_on, loan_id))


def list_history():
    return get_db().execute(SELECT_HISTORY).fetchall()


def commit():
    get_db().commit()

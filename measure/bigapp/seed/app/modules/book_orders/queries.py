"""書籍の購入の申請の SQL。"""

from app.core.db import get_db

# 在籍している社員だけを読む（総務規程 第 6 条）
SELECT_ACTIVE_EMPLOYEE = "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status = 'active'"

SELECT_REQUESTS = """
SELECT r.id, r.employee_no, e.name AS employee_name, r.quantity, r.unit_price, r.amount_incl_tax, r.state
FROM book_orders_requests r LEFT JOIN employees e ON e.employee_no = r.employee_no
{where} ORDER BY r.id
"""
SELECT_REQUEST = SELECT_REQUESTS.format(where="WHERE r.id = ?")
INSERT_REQUEST = (
    "INSERT INTO book_orders_requests (employee_no, quantity, unit_price, amount_incl_tax, state, created_on) "
    "VALUES (?, ?, ?, ?, 'pending', ?)"
)
UPDATE_STATE = "UPDATE book_orders_requests SET state = ? WHERE id = ? AND state = 'pending'"


def find_active_employee(employee_no):
    return get_db().execute(SELECT_ACTIVE_EMPLOYEE, (employee_no,)).fetchone()


def list_requests(state=None):
    if state:
        return get_db().execute(SELECT_REQUESTS.format(where="WHERE r.state = ?"), (state,)).fetchall()
    return get_db().execute(SELECT_REQUESTS.format(where="")).fetchall()


def find_request(request_id):
    return get_db().execute(SELECT_REQUEST, (request_id,)).fetchone()


def insert_request(employee_no, quantity, unit_price, amount, created_on):
    cur = get_db().execute(INSERT_REQUEST, (employee_no, quantity, unit_price, amount, created_on))
    return cur.lastrowid


def update_state(request_id, state):
    get_db().execute(UPDATE_STATE, (state, request_id))

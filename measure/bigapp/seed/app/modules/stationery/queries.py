"""文具の申請の SQL。commit は呼び出し側で行う。"""

from app.core.db import get_db

SELECT_REQUESTS = """
SELECT r.id, r.employee_no, e.name AS employee_name, r.quantity, r.unit_price, r.state
FROM stationery_requests r LEFT JOIN employees e ON e.employee_no = r.employee_no
"""


def find_employee(employee_no):
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()


def list_requests(state=None):
    """申請を id の昇順で返す。state を渡すとその状態だけ。"""
    if state:
        return get_db().execute(SELECT_REQUESTS + " WHERE r.state = ? ORDER BY r.id", (state,)).fetchall()
    return get_db().execute(SELECT_REQUESTS + " ORDER BY r.id").fetchall()


def get_request(request_id):
    return get_db().execute(SELECT_REQUESTS + " WHERE r.id = ?", (request_id,)).fetchone()


def insert_request(employee_no, quantity, unit_price):
    cur = get_db().execute(
        "INSERT INTO stationery_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, 'pending')",
        (employee_no, quantity, unit_price),
    )
    return cur.lastrowid


def set_state(request_id, state):
    get_db().execute("UPDATE stationery_requests SET state = ? WHERE id = ?", (state, request_id))

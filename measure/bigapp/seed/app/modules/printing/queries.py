"""印刷の申請の SQL。"""

from app.core.db import get_db

SELECT_ACTIVE_EMPLOYEE = "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status = 'active'"
INSERT_REQUEST = "INSERT INTO printing_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, 'pending')"
SELECT_REQUESTS = "SELECT * FROM printing_requests ORDER BY id"
SELECT_REQUESTS_BY_STATE = "SELECT * FROM printing_requests WHERE state = ? ORDER BY id"
SELECT_REQUEST = "SELECT * FROM printing_requests WHERE id = ?"
UPDATE_STATE = "UPDATE printing_requests SET state = ? WHERE id = ?"
SELECT_ACTIVE_EMPLOYEES = "SELECT employee_no, name FROM employees WHERE status = 'active' ORDER BY employee_no"
SELECT_EMPLOYEE_NAME = "SELECT name FROM employees WHERE employee_no = ?"


def find_active_employee(employee_no):
    """在籍している社員の行。退職者や存在しない番号は None。"""
    return get_db().execute(SELECT_ACTIVE_EMPLOYEE, (employee_no,)).fetchone()


def active_employees():
    return get_db().execute(SELECT_ACTIVE_EMPLOYEES).fetchall()


def employee_name(employee_no):
    row = get_db().execute(SELECT_EMPLOYEE_NAME, (employee_no,)).fetchone()
    return row["name"] if row else ""


def insert_request(employee_no, quantity, unit_price):
    """申請を 1 件足し、その id を返す（commit は呼び出し側）。"""
    return get_db().execute(INSERT_REQUEST, (employee_no, quantity, unit_price)).lastrowid


def list_requests(state=None):
    if state:
        return get_db().execute(SELECT_REQUESTS_BY_STATE, (state,)).fetchall()
    return get_db().execute(SELECT_REQUESTS).fetchall()


def find_request(request_id):
    return get_db().execute(SELECT_REQUEST, (request_id,)).fetchone()


def update_state(request_id, state):
    """申請の状態を替える（commit は呼び出し側）。"""
    get_db().execute(UPDATE_STATE, (state, request_id))

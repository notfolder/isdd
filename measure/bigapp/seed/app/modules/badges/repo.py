"""社章の申請の SQL。判定は service.py が行い、ここは読み書きだけをする。"""

from app.core.db import get_db


def find_active_employee(employee_no):
    """在籍している社員の行。退職者と存在しない番号は None。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'",
        (employee_no,),
    ).fetchone()


def insert_request(employee_no, quantity, unit_price, amount_incl_tax, created_at):
    cur = get_db().execute(
        "INSERT INTO badges_request (employee_no, quantity, unit_price, amount_incl_tax, state, created_at) "
        "VALUES (?, ?, ?, ?, 'pending', ?)",
        (employee_no, quantity, unit_price, amount_incl_tax, created_at),
    )
    return cur.lastrowid


def get_request(request_id):
    return get_db().execute(
        "SELECT r.*, e.name AS employee_name FROM badges_request r "
        "LEFT JOIN employees e ON e.employee_no = r.employee_no WHERE r.id = ?",
        (request_id,),
    ).fetchone()


def list_requests(state=None):
    sql = (
        "SELECT r.*, e.name AS employee_name FROM badges_request r "
        "LEFT JOIN employees e ON e.employee_no = r.employee_no"
    )
    args = ()
    if state:
        sql += " WHERE r.state = ?"
        args = (state,)
    return get_db().execute(sql + " ORDER BY r.id", args).fetchall()


def update_state(request_id, state):
    get_db().execute("UPDATE badges_request SET state = ? WHERE id = ?", (state, request_id))

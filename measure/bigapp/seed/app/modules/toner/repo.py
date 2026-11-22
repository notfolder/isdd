"""トナーの申請の SQL。判定は service.py に置き、ここは読み書きだけを行う。"""

from app.core import clock
from app.core.db import get_db


def find_active_employee(employee_no):
    """在籍している社員を 1 人読む。退職者と存在しない番号は None。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status = 'active'",
        (employee_no,),
    ).fetchone()


def insert_request(employee_no, quantity, unit_price):
    """申請を追加して id を返す。税込みの金額は SQL の中で計算する（1 円未満は切り捨て）。"""
    cur = get_db().execute(
        "INSERT INTO toner_requests (employee_no, quantity, unit_price, amount_excl_tax, amount_incl_tax, state, created_at) "
        "VALUES (?, ?, ?, ? * ?, CAST(? * ? * 110 / 100 AS INTEGER), 'pending', ?)",
        (employee_no, quantity, unit_price, quantity, unit_price, quantity, unit_price, clock.today().isoformat()),
    )
    return cur.lastrowid


def get_request(request_id):
    return get_db().execute(
        "SELECT r.*, e.name AS employee_name FROM toner_requests r "
        "JOIN employees e ON e.employee_no = r.employee_no WHERE r.id = ?",
        (request_id,),
    ).fetchone()


def list_requests(state=None):
    sql = (
        "SELECT r.*, e.name AS employee_name FROM toner_requests r "
        "JOIN employees e ON e.employee_no = r.employee_no"
    )
    params = ()
    if state:
        sql += " WHERE r.state = ?"
        params = (state,)
    return get_db().execute(sql + " ORDER BY r.id", params).fetchall()


def set_state(request_id, state):
    get_db().execute("UPDATE toner_requests SET state = ? WHERE id = ?", (state, request_id))


def commit():
    get_db().commit()

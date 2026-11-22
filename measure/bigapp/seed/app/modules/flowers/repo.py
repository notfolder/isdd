"""生花の申請の SQL。判定は持たず、読み書きだけを行う。"""

from dataclasses import dataclass

from app.core.db import get_db

STATES = ("pending", "approved", "rejected")
TAX_PERCENT = 10


@dataclass
class FlowerRequest:
    """申請 1 件。"""

    id: int
    employee_no: str
    employee_name: str
    quantity: int
    unit_price: int
    state: str

    @property
    def amount_excl_tax(self) -> int:
        """税抜きの金額。"""
        return self.quantity * self.unit_price

    @property
    def amount_incl_tax(self) -> int:
        """税込みの金額。消費税 10% を足し、1 円未満は切り捨てる。"""
        yen, _fraction = divmod(self.amount_excl_tax * (100 + TAX_PERCENT), 100)
        return yen


_SELECT = """
SELECT r.id, r.employee_no, e.name AS employee_name, r.quantity, r.unit_price, r.state
FROM flowers_requests r JOIN employees e ON e.employee_no = r.employee_no
"""


def _to_request(row):
    return FlowerRequest(**dict(row)) if row else None


def find_active_employee(employee_no: str):
    """在籍している社員の行。退職者と存在しない番号は None。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'",
        (employee_no,),
    ).fetchone()


def list_requests(state=None):
    sql = _SELECT + (" WHERE r.state = ?" if state else "") + " ORDER BY r.id"
    rows = get_db().execute(sql, (state,) if state else ()).fetchall()
    return [_to_request(r) for r in rows]


def get_request(request_id: int):
    return _to_request(get_db().execute(_SELECT + " WHERE r.id = ?", (request_id,)).fetchone())


def insert_request(employee_no: str, quantity: int, unit_price: int) -> int:
    cur = get_db().execute(
        "INSERT INTO flowers_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, 'pending')",
        (employee_no, quantity, unit_price),
    )
    return cur.lastrowid


def update_state(request_id: int, state: str) -> None:
    get_db().execute("UPDATE flowers_requests SET state = ? WHERE id = ?", (state, request_id))

"""クリーニングの申請の処理。申請の登録・承認・却下と、入力の確認を行う。"""

import sqlite3
from dataclasses import dataclass

STATES = ("pending", "approved", "rejected")
STATE_LABELS = {"pending": "申請中", "approved": "承認", "rejected": "却下"}
QUANTITY_RANGE = (1, 20)
UNIT_PRICE_RANGE = (1, 100000)


class RuleError(Exception):
    """きまりに合わない操作。メッセージは画面にそのまま出す。"""


@dataclass
class CleaningRequest:
    """クリーニングの申請 1 件。"""

    id: int
    employee_no: str
    employee_name: str
    quantity: int
    unit_price: int
    state: str

    @property
    def amount_excl_tax(self) -> int:
        """税抜きの金額（円）。"""
        return self.quantity * self.unit_price

    @property
    def amount_incl_tax(self) -> int:
        """税込みの金額（円）。消費税 10% を足し、1 円未満は切り捨てる。"""
        yen, _fraction = divmod(self.amount_excl_tax * 110, 100)
        return yen

    @property
    def state_label(self) -> str:
        return STATE_LABELS[self.state]


_SELECT = """
SELECT r.id, r.employee_no, e.name AS employee_name, r.quantity, r.unit_price, r.state
FROM cleaning_requests r JOIN employees e ON e.employee_no = r.employee_no
"""


def _to_request(row) -> CleaningRequest:
    return CleaningRequest(row["id"], row["employee_no"], row["employee_name"], row["quantity"], row["unit_price"], row["state"])


def parse_int(text, label: str, low: int, high: int) -> int:
    """半角数字だけの整数を読み、範囲外なら RuleError にする。"""
    text = (text or "").strip()
    if not (text.isascii() and text.isdigit()):
        raise RuleError(f"{label}は整数で入力してください")
    value = int(text)
    if not low <= value <= high:
        raise RuleError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def list_requests(conn: sqlite3.Connection, state=None) -> list:
    sql = _SELECT + (" WHERE r.state = ?" if state else "") + " ORDER BY r.id"
    rows = conn.execute(sql, (state,) if state else ()).fetchall()
    return [_to_request(r) for r in rows]


def get_request(conn: sqlite3.Connection, request_id):
    """申請 1 件。無ければ None。"""
    text = (request_id or "").strip()
    if not (text.isascii() and text.isdigit()):
        return None
    row = conn.execute(_SELECT + " WHERE r.id = ?", (int(text),)).fetchone()
    return _to_request(row) if row else None


def apply(conn: sqlite3.Connection, employee_no, quantity, unit_price) -> int:
    """申請を登録し、申請の id を返す。対象は在籍している社員だけ。"""
    employee_no = (employee_no or "").strip()
    employee = conn.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise RuleError("社員が見つかりません")
    in_service = employee["status"] != "retired"  # 在籍の判定は「退職していない」
    if not in_service:
        raise RuleError("退職した社員は申請できません")
    qty = parse_int(quantity, "数量", *QUANTITY_RANGE)
    price = parse_int(unit_price, "単価", *UNIT_PRICE_RANGE)
    cursor = conn.execute(
        "INSERT INTO cleaning_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, 'pending')",
        (employee_no, qty, price),
    )
    return cursor.lastrowid


def _pending(conn, request_id) -> CleaningRequest:
    target = get_request(conn, request_id)
    if target is None:
        raise RuleError("申請が見つかりません")
    if target.state != "pending":
        raise RuleError("申請中の申請だけが対象です")
    return target


def approve(conn: sqlite3.Connection, request_id, approver_no: str) -> int:
    """承認する。承認者が申請した本人のときは承認できない。"""
    target = _pending(conn, request_id)
    if target.employee_no == approver_no:
        raise RuleError("自分の申請は承認できません")
    conn.execute("UPDATE cleaning_requests SET state = 'approved' WHERE id = ?", (target.id,))
    return target.id


def reject(conn: sqlite3.Connection, request_id) -> int:
    """却下する。申請した本人でも却下はできる。"""
    target = _pending(conn, request_id)
    conn.execute("UPDATE cleaning_requests SET state = 'rejected' WHERE id = ?", (target.id,))
    return target.id

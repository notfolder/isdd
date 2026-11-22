"""名刺の申請の処理（総務規程 第 5 条・第 6 条）。"""

from dataclasses import dataclass
from typing import Optional

from app.core.db import get_db

QUANTITY_MIN, QUANTITY_MAX = 1, 500
UNIT_PRICE_MIN, UNIT_PRICE_MAX = 1, 100000
STATES = ("pending", "approved", "rejected")


class RequestError(Exception):
    """受け付けられない理由。画面にそのまま出す。"""


@dataclass
class CardRequest:
    """名刺の申請 1 件。"""

    id: int
    employee_no: str
    employee_name: str
    quantity: int
    unit_price: int
    state: str

    @property
    def amount_excl_tax(self) -> int:
        return self.quantity * self.unit_price

    @property
    def amount_incl_tax(self) -> int:
        return tax_included(self.quantity, self.unit_price)


def tax_included(quantity: int, unit_price: int) -> int:
    """税込みの金額。消費税 10% を足し、1 円未満は切り捨てる（整数で計算する）。"""
    return quantity * unit_price * 110 // 100


def parse_int(text: Optional[str], low: int, high: int, label: str) -> int:
    """半角数字だけの整数を読み、範囲外なら理由つきで拒否する。"""
    text = (text or "").strip()
    if not (text.isascii() and text.isdigit()):
        raise RequestError(f"{label}は整数で入力してください")
    value = int(text)
    if not low <= value <= high:
        raise RequestError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def _to_request(row) -> CardRequest:
    return CardRequest(row["id"], row["employee_no"], row["name"], row["quantity"], row["unit_price"], row["state"])


_SELECT = (
    "SELECT r.id, r.employee_no, e.name, r.quantity, r.unit_price, r.state "
    "FROM business_cards_requests r JOIN employees e ON e.employee_no = r.employee_no"
)


def list_requests(state: Optional[str] = None) -> list:
    """申請を id の昇順で返す。state を渡すとその状態だけ。"""
    if state:
        rows = get_db().execute(_SELECT + " WHERE r.state = ? ORDER BY r.id", (state,)).fetchall()
    else:
        rows = get_db().execute(_SELECT + " ORDER BY r.id").fetchall()
    return [_to_request(r) for r in rows]


def get_request(request_id: Optional[str]) -> Optional[CardRequest]:
    """申請 1 件。数字でない・存在しないときは None。"""
    text = (request_id or "").strip()
    if not (text.isascii() and text.isdigit()):
        return None
    row = get_db().execute(_SELECT + " WHERE r.id = ?", (int(text),)).fetchone()
    return _to_request(row) if row else None


def apply(employee_no: str, quantity_text: Optional[str], unit_price_text: Optional[str]) -> int:
    """申請を作り、id を返す。在籍していない社員は対象にしない。"""
    employee = get_db().execute("SELECT status FROM employees WHERE employee_no = ?", ((employee_no or "").strip(),)).fetchone()
    if employee is None:
        raise RequestError("社員が見つかりません")
    if employee["status"] == "retired":
        raise RequestError("退職した社員は申請できません")
    quantity = parse_int(quantity_text, QUANTITY_MIN, QUANTITY_MAX, "数量")
    unit_price = parse_int(unit_price_text, UNIT_PRICE_MIN, UNIT_PRICE_MAX, "単価")
    cur = get_db().execute(
        "INSERT INTO business_cards_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, 'pending')",
        ((employee_no or "").strip(), quantity, unit_price),
    )
    return cur.lastrowid


def _pending(request_id: Optional[str]) -> CardRequest:
    req = get_request(request_id)
    if req is None:
        raise RequestError("申請が見つかりません")
    if req.state != "pending":
        raise RequestError("申請中の申請だけが対象です")
    return req


def approve(request_id: Optional[str], approver_no: str) -> CardRequest:
    """承認する。申請中のものだけ。申請した本人は承認できない（総務規程 第 5 条）。"""
    req = _pending(request_id)
    if req.employee_no == approver_no:
        raise RequestError("自分の申請は承認できません")
    get_db().execute("UPDATE business_cards_requests SET state = 'approved' WHERE id = ?", (req.id,))
    return req


def reject(request_id: Optional[str]) -> CardRequest:
    """却下する。申請中のものだけ（本人による却下はできる）。"""
    req = _pending(request_id)
    get_db().execute("UPDATE business_cards_requests SET state = 'rejected' WHERE id = ?", (req.id,))
    return req


def active_employees() -> list:
    """申請できる社員（退職していない社員）。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE status != 'retired' ORDER BY employee_no"
    ).fetchall()

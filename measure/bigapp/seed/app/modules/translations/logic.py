"""翻訳の申請の処理。数量と単価の検証、税込み金額の計算、承認と却下の判定を持つ。"""

import re
from dataclasses import dataclass
from typing import Optional

from app.core.db import get_db

# 数量と単価の範囲
MIN_QUANTITY = 1
MAX_QUANTITY = 50
MIN_UNIT_PRICE = 1
MAX_UNIT_PRICE = 100000

# 消費税率（%）
TAX_RATE_PERCENT = 10

# 申請の対象にできない社員の状態（退職）
EXCLUDED_STATUSES = {"retired"}

# 申請の状態
PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
STATES = (PENDING, APPROVED, REJECTED)

_INTEGER = re.compile(r"[0-9]+")


class RequestError(Exception):
    """申請を受け付けられないときの理由。画面にそのまま出す。"""


@dataclass
class TranslationRequest:
    """翻訳の申請 1 件。"""

    id: int
    employee_no: str
    employee_name: str
    quantity: int
    unit_price: int
    state: str

    @property
    def subtotal(self) -> int:
        """税抜きの金額。"""
        return self.quantity * self.unit_price

    @property
    def amount_incl_tax(self) -> int:
        """税込みの金額（1 円未満は切り捨て）。"""
        return calc_amount_incl_tax(self.quantity, self.unit_price)


def calc_amount_incl_tax(quantity: int, unit_price: int) -> int:
    """数量 × 単価に消費税を足し、1 円未満を切り捨てた金額を返す。"""
    subtotal = quantity * unit_price
    return subtotal * (100 + TAX_RATE_PERCENT) // 100


def parse_int(text: Optional[str], label: str, low: int, high: int) -> int:
    """入力欄の文字列を整数にして範囲を確かめる。"""
    value = (text or "").strip()
    if not _INTEGER.fullmatch(value):
        raise RequestError(f"{label}は整数で入力してください")
    number = int(value)
    if not low <= number <= high:
        raise RequestError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return number


def _to_request(row) -> TranslationRequest:
    return TranslationRequest(
        id=row["id"],
        employee_no=row["employee_no"],
        employee_name=row["employee_name"] or "",
        quantity=row["quantity"],
        unit_price=row["unit_price"],
        state=row["state"],
    )


_SELECT = (
    "SELECT r.id, r.employee_no, e.name AS employee_name, r.quantity, r.unit_price, r.state "
    "FROM translations_requests r LEFT JOIN employees e ON e.employee_no = r.employee_no"
)


def list_requests(state: Optional[str] = None) -> list:
    """申請の一覧（id の昇順）。state を渡すとその状態だけ。"""
    if state:
        rows = get_db().execute(_SELECT + " WHERE r.state = ? ORDER BY r.id", (state,)).fetchall()
    else:
        rows = get_db().execute(_SELECT + " ORDER BY r.id").fetchall()
    return [_to_request(r) for r in rows]


def get_request(request_id: int) -> Optional[TranslationRequest]:
    row = get_db().execute(_SELECT + " WHERE r.id = ?", (request_id,)).fetchone()
    return _to_request(row) if row else None


def parse_request_id(text: Optional[str]) -> int:
    value = (text or "").strip()
    if not _INTEGER.fullmatch(value):
        raise RequestError("申請が見つかりません")
    return int(value)


def check_target_employee(employee_no: str) -> None:
    """申請できる社員か確かめる（在籍していること）。"""
    row = get_db().execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if row is None:
        raise RequestError("社員が見つかりません")
    if row["status"] in EXCLUDED_STATUSES:
        raise RequestError("退職した社員は申請できません")


def apply(employee_no: str, quantity_text: Optional[str], unit_price_text: Optional[str]) -> int:
    """申請を登録して id を返す。受け付けないときは RequestError。commit は呼び出し側。"""
    employee_no = (employee_no or "").strip()
    check_target_employee(employee_no)
    quantity = parse_int(quantity_text, "数量", MIN_QUANTITY, MAX_QUANTITY)
    unit_price = parse_int(unit_price_text, "単価", MIN_UNIT_PRICE, MAX_UNIT_PRICE)
    cursor = get_db().execute(
        "INSERT INTO translations_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, ?)",
        (employee_no, quantity, unit_price, PENDING),
    )
    return cursor.lastrowid


def _pending_request(request_id_text: Optional[str]) -> TranslationRequest:
    req = get_request(parse_request_id(request_id_text))
    if req is None:
        raise RequestError("申請が見つかりません")
    if req.state != PENDING:
        raise RequestError("申請中の申請だけが対象です")
    return req


def approve(request_id_text: Optional[str], approver_no: str) -> int:
    """申請を承認する。申請した本人は承認できない。"""
    req = _pending_request(request_id_text)
    if req.employee_no == approver_no:
        raise RequestError("自分の申請は承認できません")
    get_db().execute("UPDATE translations_requests SET state = ? WHERE id = ?", (APPROVED, req.id))
    return req.id


def reject(request_id_text: Optional[str]) -> int:
    """申請を却下する。本人による却下はできる。"""
    req = _pending_request(request_id_text)
    get_db().execute("UPDATE translations_requests SET state = ? WHERE id = ?", (REJECTED, req.id))
    return req.id

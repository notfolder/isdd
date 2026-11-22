"""名札の申請の判定。受け付けないときは RequestError を投げ、画面側で受ける。"""

import re
from decimal import ROUND_DOWN, Decimal

QUANTITY_MIN, QUANTITY_MAX = 1, 100
PRICE_MIN, PRICE_MAX = 1, 100000
TAX_RATE = Decimal("0.10")  # 消費税 10%
STATES = ("pending", "approved", "rejected")


class RequestError(Exception):
    """入力を受け付けないときの例外。メッセージは画面に出す理由。"""


def parse_int(text, label, low, high):
    """半角数字の整数として読み、範囲を確かめる。"""
    text = (text or "").strip()
    if not re.fullmatch(r"[0-9]+", text):
        raise RequestError(f"{label}は整数で入力してください")
    value = int(text)
    if not (low <= value <= high):
        raise RequestError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def gross_amount(quantity: int, unit_price: int) -> int:
    """税込みの金額。数量 × 単価に消費税 10% を足し、1 円未満を切り捨てる。"""
    net = Decimal(quantity) * Decimal(unit_price)
    return int((net * (Decimal(1) + TAX_RATE)).quantize(Decimal(1), rounding=ROUND_DOWN))


def net_amount(quantity: int, unit_price: int) -> int:
    """税抜きの金額。"""
    return quantity * unit_price


def check_applicant(employee):
    """申請の対象は在籍している社員だけ。"""
    if employee is None:
        raise RequestError("社員が見つかりません")
    if employee["status"] != "active":
        raise RequestError("退職した社員は申請できません")


def check_decidable(request_row, actor_no, approving):
    """承認・却下できるかを確かめる。申請中のものだけ。本人は承認できない（却下はできる）。"""
    if request_row is None:
        raise RequestError("申請が見つかりません")
    if request_row["state"] != "pending":
        raise RequestError("申請中の申請だけ承認・却下できます")
    if approving and request_row["employee_no"] == actor_no:
        raise RequestError("自分の申請は承認できません")

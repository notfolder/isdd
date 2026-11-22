"""宅配便の申請の判定。受け付けないときは CourierError を投げ、画面側で受ける。"""

import re

from app.core import clock
from app.core.db import get_db

# 消費税率（%）
TAX_RATE_PERCENT = 10

QUANTITY_MIN, QUANTITY_MAX = 1, 30
UNIT_PRICE_MIN, UNIT_PRICE_MAX = 1, 100000

STATES = ("pending", "approved", "rejected")


class CourierError(Exception):
    """入力を受け付けないときの例外。メッセージは画面に出す理由。"""


def _parse_int(text, label, low, high):
    """半角数字だけの整数を読み、範囲を確かめる。"""
    value = (text or "").strip()
    if not re.fullmatch(r"[0-9]+", value):
        raise CourierError(f"{label}は整数で入力してください")
    number = int(value)
    if not (low <= number <= high):
        raise CourierError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return number


def amount_incl_tax(quantity, unit_price):
    """税込みの金額。数量 × 単価に消費税を足し、1 円未満は切り捨てる。"""
    subtotal = quantity * unit_price
    return subtotal * (100 + TAX_RATE_PERCENT) // 100


def apply(employee_no, quantity_text, unit_price_text):
    """申請を登録し、申請の id を返す。在籍していない社員は受け付けない。"""
    employee = (employee_no or "").strip()
    row = get_db().execute(
        "SELECT employee_no FROM employees WHERE employee_no = ? AND status <> 'retired'", (employee,)
    ).fetchone()
    if row is None:
        raise CourierError("在籍している社員が見つかりません")
    quantity = _parse_int(quantity_text, "数量", QUANTITY_MIN, QUANTITY_MAX)
    unit_price = _parse_int(unit_price_text, "単価", UNIT_PRICE_MIN, UNIT_PRICE_MAX)
    cursor = get_db().execute(
        "INSERT INTO courier_requests (employee_no, quantity, unit_price, amount_incl_tax, state, created_on)"
        " VALUES (?, ?, ?, ?, 'pending', ?)",
        (employee, quantity, unit_price, amount_incl_tax(quantity, unit_price), clock.today().isoformat()),
    )
    return cursor.lastrowid


def get_request(request_id_text):
    """申請 1 件を返す。無ければ CourierError。"""
    value = (request_id_text or "").strip()
    row = None
    if re.fullmatch(r"[0-9]+", value):
        row = get_db().execute("SELECT * FROM courier_requests WHERE id = ?", (int(value),)).fetchone()
    if row is None:
        raise CourierError("申請が見つかりません")
    return row


def approve(request_id_text, approver_no):
    """申請中の申請を承認する。申請した本人は承認できない。"""
    row = get_request(request_id_text)
    if row["state"] != "pending":
        raise CourierError("申請中のものだけ承認できます")
    if row["employee_no"] == approver_no:
        raise CourierError("自分の申請は承認できません")
    get_db().execute("UPDATE courier_requests SET state = 'approved' WHERE id = ?", (row["id"],))
    return row["id"]


def reject(request_id_text):
    """申請中の申請を却下する。申請した本人でも却下はできる。"""
    row = get_request(request_id_text)
    if row["state"] != "pending":
        raise CourierError("申請中のものだけ却下できます")
    get_db().execute("UPDATE courier_requests SET state = 'rejected' WHERE id = ?", (row["id"],))
    return row["id"]


def list_requests(state=None):
    """申請の一覧（id の昇順）。state を指定するとその状態だけ。"""
    if state:
        if state not in STATES:
            raise CourierError("状態が正しくありません")
        return get_db().execute("SELECT * FROM courier_requests WHERE state = ? ORDER BY id", (state,)).fetchall()
    return get_db().execute("SELECT * FROM courier_requests ORDER BY id").fetchall()

"""消耗品の申請の判定。受け付けないときは SuppliesError を投げ、画面側（web.py）で受ける。"""

import math

from app.core.db import get_db

MAX_QUANTITY = 100
MAX_UNIT_PRICE = 100000


class SuppliesError(Exception):
    """入力を受け付けないときの例外。メッセージは画面にそのまま出す。"""


def parse_int(text, label, low, high):
    """整数の入力を読む。整数でない、または範囲外なら受け付けない。"""
    text = (text or "").strip()
    try:
        value = int(text)
    except ValueError:
        raise SuppliesError(f"{label}は整数で入力してください")
    if not low <= value <= high:
        raise SuppliesError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def apply(employee_no, quantity_text, unit_price_text):
    """申請を 1 件作り、その id を返す。税込みの金額は数量 × 単価 × 1.1 の 1 円未満切り捨て。"""
    quantity = parse_int(quantity_text, "数量", 1, MAX_QUANTITY)
    unit_price = parse_int(unit_price_text, "単価", 1, MAX_UNIT_PRICE)
    # 在籍している社員だけが対象（退職者と存在しない社員番号は受け付けない）
    employee = get_db().execute(
        "SELECT employee_no FROM employees WHERE employee_no = ? AND status <> 'retired'",
        (employee_no,),
    ).fetchone()
    if employee is None:
        raise SuppliesError("在籍している社員を指定してください")
    amount_incl_tax = math.floor(quantity * unit_price * 1.1)
    cursor = get_db().execute(
        "INSERT INTO supplies_requests (employee_no, quantity, unit_price, amount_incl_tax, state) "
        "VALUES (?, ?, ?, ?, 'pending')",
        (employee["employee_no"], quantity, unit_price, amount_incl_tax),
    )
    return cursor.lastrowid


def find_request(request_id_text):
    """申請を 1 件読む。見つからなければ受け付けない。"""
    text = (request_id_text or "").strip()
    row = None
    if text.isdigit():
        row = get_db().execute("SELECT * FROM supplies_requests WHERE id = ?", (int(text),)).fetchone()
    if row is None:
        raise SuppliesError("申請が見つかりません")
    return row


def approve(request_id_text, approver_no):
    """申請中の申請を承認する。申請した本人は承認できない。"""
    row = find_request(request_id_text)
    if row["state"] != "pending":
        raise SuppliesError("申請中の申請だけ承認できます")
    if row["employee_no"] == approver_no:
        raise SuppliesError("自分の申請は承認できません")
    get_db().execute("UPDATE supplies_requests SET state = 'approved' WHERE id = ?", (row["id"],))
    return row["id"]


def reject(request_id_text):
    """申請中の申請を却下する。申請した本人が却下するのは構わない。"""
    row = find_request(request_id_text)
    if row["state"] != "pending":
        raise SuppliesError("申請中の申請だけ却下できます")
    get_db().execute("UPDATE supplies_requests SET state = 'rejected' WHERE id = ?", (row["id"],))
    return row["id"]

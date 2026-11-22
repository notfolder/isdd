"""文具の申請の判定。画面や DB には触れず、値だけで判定する。"""

import re

QUANTITY_MIN, QUANTITY_MAX = 1, 100
UNIT_PRICE_MIN, UNIT_PRICE_MAX = 1, 100000
STATES = ("pending", "approved", "rejected")


def parse_int(text, low, high):
    """半角数字だけの文字列を整数にする。範囲外や数字以外は None。"""
    text = (text or "").strip()
    if not re.fullmatch(r"[0-9]+", text):
        return None
    value = int(text)
    return value if low <= value <= high else None


def subtotal(quantity, unit_price):
    """税抜きの金額。"""
    return quantity * unit_price


def total(quantity, unit_price):
    """税込みの金額。税額（10%）を先に出し、1 円未満は切り捨てて足す。"""
    sub = subtotal(quantity, unit_price)
    tax = sub * 10 // 100
    return sub + tax


def is_active(employee):
    """在籍している社員か。"""
    return employee is not None and employee["status"] == "active"


def check_apply(employee, quantity_text, unit_price_text):
    """申請の入力を確かめる。(数量, 単価, エラー文) を返す。"""
    if employee is None:
        return None, None, "社員が見つかりません"
    if not is_active(employee):
        return None, None, "退職した社員は申請できません"
    quantity = parse_int(quantity_text, QUANTITY_MIN, QUANTITY_MAX)
    if quantity is None:
        return None, None, "数量は 1 以上 100 以下の整数で入力してください"
    unit_price = parse_int(unit_price_text, UNIT_PRICE_MIN, UNIT_PRICE_MAX)
    if unit_price is None:
        return None, None, "単価は 1 以上 100000 以下の整数で入力してください"
    return quantity, unit_price, None


def check_decision(request_row, action, actor_no):
    """承認・却下できるかを確かめる。できなければエラー文、できれば None。"""
    if request_row is None:
        return "申請が見つかりません"
    if request_row["state"] != "pending":
        return "申請中の申請だけが対象です"
    if action == "approve" and request_row["employee_no"] == actor_no:
        return "自分の申請は承認できません"
    return None

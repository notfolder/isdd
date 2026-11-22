"""乗車券の申請の判定。不正な入力は RuleError を投げ、画面側で受けて 400 にする。"""

import re

QUANTITY_MIN, QUANTITY_MAX = 1, 40
PRICE_MIN, PRICE_MAX = 1, 100000
STATES = ("pending", "approved", "rejected")


class RuleError(Exception):
    """業務のきまりに反する操作。メッセージは画面にそのまま出す。"""


def parse_int(text, label, low, high):
    """整数の入力を読み、範囲（low 以上 high 以下）を確かめる。"""
    text = (text or "").strip()
    if not re.fullmatch(r"[0-9]+", text):
        raise RuleError(f"{label}は整数で入力してください")
    value = int(text)
    if not (low <= value <= high):
        raise RuleError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def tax_included(quantity, unit_price):
    """税込みの金額。数量 × 単価に消費税 10% を足し、1 円未満は切り捨てる。"""
    return quantity * unit_price * 110 // 100


def check_employee(employee):
    """対象にできるのは在籍している社員だけ（総務規程 第 6 条）。"""
    if employee is None:
        raise RuleError("社員が見つかりません")
    if employee["status"] != "active":
        raise RuleError("退職した社員は対象にできません")


def check_pending(request_row):
    """承認と却下は申請中のものだけにできる。"""
    if request_row is None:
        raise RuleError("申請が見つかりません")
    if request_row["state"] != "pending":
        raise RuleError("申請中の申請だけが対象です")


def check_can_approve(request_row, approver_no):
    """申請した本人は自分の申請を承認できない（総務規程 第 5 条）。却下はできる。"""
    check_pending(request_row)
    if request_row["employee_no"] == approver_no:
        raise RuleError("自分の申請は承認できません")

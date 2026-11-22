"""社章の申請の判定と処理。総務規程 第 5 条・第 6 条・第 7 条にもとづく。"""

from app.core import audit, clock
from app.modules.badges import repo

STATES = ("pending", "approved", "rejected")
STATE_LABELS = {"pending": "申請中", "approved": "承認", "rejected": "却下"}
QUANTITY_MAX = 50
UNIT_PRICE_MAX = 100000


class Rejected(Exception):
    """受け付けない理由を持つ例外。画面には理由をそのまま出す。"""


def tax_included(quantity, unit_price):
    """税込み金額。消費税 10% を足し、1 円未満は切り捨てる（整数の計算だけで行う）。"""
    return quantity * unit_price * 110 // 100


def _parse_int(text, name, low, high):
    """半角数字だけの整数を読み、low 以上 high 以下か確かめる。"""
    text = (text or "").strip()
    if not (text.isascii() and text.isdigit()):
        raise Rejected(f"{name}は整数で入力してください")
    value = int(text)
    if not low <= value <= high:
        raise Rejected(f"{name}は {low} 以上 {high} 以下で入力してください")
    return value


def apply(employee_no, quantity_text, unit_price_text):
    """申請する。受け付けないときは Rejected。"""
    employee_no = (employee_no or "").strip()
    if repo.find_active_employee(employee_no) is None:
        raise Rejected("在籍している社員を指定してください")
    quantity = _parse_int(quantity_text, "数量", 1, QUANTITY_MAX)
    unit_price = _parse_int(unit_price_text, "単価", 1, UNIT_PRICE_MAX)
    created_at = clock.today().isoformat()
    request_id = repo.insert_request(employee_no, quantity, unit_price, tax_included(quantity, unit_price), created_at)
    audit.record("badges", "apply", str(request_id))
    return request_id


def _pending_request(request_id_text):
    """申請中の申請を返す。存在しない・申請中でないときは Rejected。"""
    text = (request_id_text or "").strip()
    row = repo.get_request(int(text)) if text.isascii() and text.isdigit() else None
    if row is None:
        raise Rejected("申請が見つかりません")
    if row["state"] != "pending":
        raise Rejected("申請中の申請だけが対象です")
    return row


def approve(request_id_text, approver_no):
    """承認する。申請した本人は承認できない。"""
    row = _pending_request(request_id_text)
    if row["employee_no"] == approver_no:
        raise Rejected("自分の申請は承認できません")
    repo.update_state(row["id"], "approved")
    audit.record("badges", "approve", str(row["id"]))


def reject(request_id_text):
    """却下する。本人の申請でも却下はできる。"""
    row = _pending_request(request_id_text)
    repo.update_state(row["id"], "rejected")
    audit.record("badges", "reject", str(row["id"]))


def show(request_id_text):
    text = (request_id_text or "").strip()
    row = repo.get_request(int(text)) if text.isascii() and text.isdigit() else None
    if row is None:
        raise Rejected("申請が見つかりません")
    return row


def list_for_screen(state):
    if state and state not in STATES:
        raise Rejected("状態が正しくありません")
    return repo.list_requests(state or None)

"""トナーの申請の判定と処理。受け付けないときは RejectedError を投げる。"""

from app.core import audit
from app.modules.toner import repo

STATES = ("pending", "approved", "rejected")
QUANTITY_MAX = 10
UNIT_PRICE_MAX = 100000


class RejectedError(Exception):
    """受け付けない理由を画面に出すための例外。"""


def _parse_int(text, label, low, high):
    """半角数字だけの整数を読み、範囲を確かめる。"""
    text = (text or "").strip()
    if not (text.isascii() and text.isdigit()):
        raise RejectedError(f"{label}は整数で入力してください")
    value = int(text)
    if not low <= value <= high:
        raise RejectedError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def check_state(state):
    if state and state not in STATES:
        raise RejectedError("状態が正しくありません")


def apply(employee_no, quantity_text, unit_price_text):
    """申請を受け付ける。申請の id を返す。"""
    quantity = _parse_int(quantity_text, "数量", 1, QUANTITY_MAX)
    unit_price = _parse_int(unit_price_text, "単価", 1, UNIT_PRICE_MAX)
    if repo.find_active_employee((employee_no or "").strip()) is None:
        raise RejectedError("在籍している社員を指定してください")
    request_id = repo.insert_request(employee_no.strip(), quantity, unit_price)
    audit.record("toner", "apply", str(request_id))
    repo.commit()
    return request_id


def _pending_request(request_id_text):
    text = (request_id_text or "").strip()
    row = repo.get_request(int(text)) if text.isascii() and text.isdigit() else None
    if row is None:
        raise RejectedError("申請が見つかりません")
    if row["state"] != "pending":
        raise RejectedError("申請中のものだけ承認・却下できます")
    return row


def approve(request_id_text, user):
    """承認する。申請した本人は承認できない。"""
    row = _pending_request(request_id_text)
    if row["employee_no"] == user["employee_no"]:
        raise RejectedError("自分の申請は承認できません")
    repo.set_state(row["id"], "approved")
    audit.record("toner", "approve", str(row["id"]))
    repo.commit()


def reject(request_id_text):
    """却下する。本人の申請でも却下できる。"""
    row = _pending_request(request_id_text)
    repo.set_state(row["id"], "rejected")
    audit.record("toner", "reject", str(row["id"]))
    repo.commit()

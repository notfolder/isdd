"""生花の申請の判定と処理。受け付けないときは RejectedInput を上げる。"""

import re

from app.core import audit
from app.core.auth import current_user
from app.core.db import get_db
from app.modules.flowers import repo

QUANTITY_RANGE = (1, 10)
UNIT_PRICE_RANGE = (1, 100000)


class RejectedInput(Exception):
    """入力を受け付けない。message は画面に出す理由。"""


def _parse_int(text, label: str, low: int, high: int) -> int:
    text = (text or "").strip()
    if not re.fullmatch(r"[0-9]+", text):
        raise RejectedInput(f"{label}は整数で入力してください")
    value = int(text)
    if not low <= value <= high:
        raise RejectedInput(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def _pending_request(request_id_text):
    """操作の対象の申請。存在しないか申請中でなければ受け付けない。"""
    text = (request_id_text or "").strip()
    request = repo.get_request(int(text)) if re.fullmatch(r"[0-9]{1,18}", text) else None
    if request is None:
        raise RejectedInput("申請が見つかりません")
    if request.state != "pending":
        raise RejectedInput("申請中の申請だけ承認・却下できます")
    return request


def apply(employee_no, quantity_text, unit_price_text) -> int:
    employee = repo.find_active_employee((employee_no or "").strip())
    if employee is None:
        raise RejectedInput("在籍している社員を指定してください")
    quantity = _parse_int(quantity_text, "数量", *QUANTITY_RANGE)
    unit_price = _parse_int(unit_price_text, "単価", *UNIT_PRICE_RANGE)
    request_id = repo.insert_request(employee["employee_no"], quantity, unit_price)
    audit.record("flowers", "apply", str(request_id))
    get_db().commit()
    return request_id


def approve(request_id_text) -> None:
    request = _pending_request(request_id_text)
    if request.employee_no == current_user()["employee_no"]:
        raise RejectedInput("自分の申請は承認できません")
    repo.update_state(request.id, "approved")
    audit.record("flowers", "approve", str(request.id))
    get_db().commit()


def reject(request_id_text) -> None:
    request = _pending_request(request_id_text)
    repo.update_state(request.id, "rejected")
    audit.record("flowers", "reject", str(request.id))
    get_db().commit()


def list_requests(state):
    """state が空なら全件。状態として正しくない値は結果が空になる。"""
    return repo.list_requests(state or None)


def get_request(request_id_text):
    text = (request_id_text or "").strip()
    return repo.get_request(int(text)) if re.fullmatch(r"[0-9]{1,18}", text) else None

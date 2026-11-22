"""制服の貸与の判定と処理。入力を受け付けないときは ServiceError を投げる。"""

import datetime

from app.core import audit, clock
from app.modules.uniforms import repo

LOAN_DAYS = 60  # 貸出の期間（日）
MAX_ACTIVE_LOANS = 2  # 1 人が同時に借りられる件数


class ServiceError(Exception):
    """入力を受け付けない理由（画面にそのまま出す）。"""


def late_days(due_on, today):
    """期限を何日過ぎているか。today - due_on の timedelta の日数（期限内は 0 以下）。"""
    return (today - due_on).days


def is_late_return(due_on, today):
    """返却の期限を過ぎているか（今日 > 期限）。"""
    return late_days(due_on, today) >= 1


def _parse_date(text):
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise ServiceError("日付は YYYY-MM-DD の形で入力してください")


def _require_item(code):
    item = repo.find_item(code)
    if item is None:
        raise ServiceError("その番号の物が見つかりません")
    return item


def _require_active_employee(employee_no):
    """在籍している（退職していない）社員だけを対象にする。"""
    employee = repo.find_employee(employee_no)
    if employee is None:
        raise ServiceError("社員が見つかりません")
    if employee["status"] != "retired":
        return employee
    raise ServiceError("退職した社員は対象にできません")


def create_item(code, name):
    code, name = code.strip(), name.strip()
    if not code:
        raise ServiceError("番号を入力してください")
    if not name:
        raise ServiceError("名前を入力してください")
    if repo.find_item(code):
        raise ServiceError("この番号は既に登録されています")
    repo.insert_item(code, name)
    audit.record("uniforms", "item_create", code)


def update_item(code, name):
    code, name = code.strip(), name.strip()
    _require_item(code)
    if not name:
        raise ServiceError("名前を入力してください")
    repo.update_item(code, name)
    audit.record("uniforms", "item_update", code)


def delete_item(code):
    code = code.strip()
    _require_item(code)
    if repo.open_loan_for_item(code):
        raise ServiceError("貸出中の物は削除できません")
    repo.delete_item(code)
    audit.record("uniforms", "item_delete", code)


def lend(item_code, employee_no, lent_on_text):
    item_code, employee_no = item_code.strip(), employee_no.strip()
    today = clock.today()
    _require_item(item_code)
    _require_active_employee(employee_no)
    lent_on = _parse_date(lent_on_text.strip()) if lent_on_text and lent_on_text.strip() else today
    if lent_on > today:
        raise ServiceError("貸出日に未来の日付は指定できません")
    if repo.open_loan_for_item(item_code):
        raise ServiceError("貸出中の物は貸せません")
    loans = repo.open_loans_of_employee(employee_no)
    for loan in loans:
        if is_late_return(datetime.date.fromisoformat(loan["due_on"]), today):
            raise ServiceError("返却の期限を過ぎた貸出があるため、新しく貸せません")
    if len(loans) >= MAX_ACTIVE_LOANS:
        raise ServiceError(f"同時に借りられるのは {MAX_ACTIVE_LOANS} 件までです")
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    repo.insert_loan(item_code, employee_no, lent_on.isoformat(), due_on.isoformat())
    audit.record("uniforms", "lend", item_code)


def return_item(item_code):
    item_code = item_code.strip()
    _require_item(item_code)
    loan = repo.open_loan_for_item(item_code)
    if loan is None:
        raise ServiceError("貸出中ではありません")
    repo.close_loan(loan["id"], clock.today().isoformat())
    audit.record("uniforms", "return", item_code)


def item_status(row, today):
    """free / lent / overdue のどれか。"""
    if row["borrower"] is None:
        return "free"
    due_on = datetime.date.fromisoformat(row["due_on"])
    return "overdue" if is_late_return(due_on, today) else "lent"


def status_rows(query=""):
    today = clock.today()
    return [(row, item_status(row, today)) for row in repo.list_items_with_loans(query)]

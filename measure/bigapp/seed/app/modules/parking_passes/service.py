"""駐車許可証の貸出の判定と処理。入力を受け付けないときは RejectedError を投げる。"""

import datetime

from app.core import audit, clock
from app.core.db import get_db
from app.modules.parking_passes import repo

LOAN_DAYS = 30  # 貸出の期間（日）


class RejectedError(Exception):
    """入力を受け付けないこと。メッセージは画面に出す理由。"""


def _text(value):
    return (value or "").strip()


def late_return(due_on, today):
    """返却の期限を過ぎているか。期限の翌日から延滞。"""
    return (today - datetime.date.fromisoformat(due_on)).days >= 1


def item_status(due_on, borrower, today):
    if borrower is None:
        return "free"
    return "overdue" if late_return(due_on, today) else "lent"


def create_item(code, name):
    code, name = _text(code), _text(name)
    if not code or not name:
        raise RejectedError("番号と名前を入力してください")
    if repo.find_item(code):
        raise RejectedError("この番号は既に登録されています")
    repo.insert_item(code, name)
    audit.record("parking_passes", "item_create", code)
    get_db().commit()


def update_item(code, name):
    code, name = _text(code), _text(name)
    if not name:
        raise RejectedError("名前を入力してください")
    if repo.find_item(code) is None:
        raise RejectedError("物が見つかりません")
    repo.update_item_name(code, name)
    audit.record("parking_passes", "item_update", code)
    get_db().commit()


def delete_item(code):
    code = _text(code)
    if repo.find_item(code) is None:
        raise RejectedError("物が見つかりません")
    if repo.open_loan_of_item(code):
        raise RejectedError("貸出中の物は削除できません")
    repo.delete_item(code)
    audit.record("parking_passes", "item_delete", code)
    get_db().commit()


def lend(item_code, employee_no, lent_on_text):
    today = clock.today()
    item = repo.find_item(_text(item_code))
    if item is None:
        raise RejectedError("物が見つかりません")
    employee_no = _text(employee_no)
    if repo.find_active_employee(employee_no) is None:
        raise RejectedError("在籍している社員ではありません")
    lent_on_text = _text(lent_on_text)
    if lent_on_text:
        try:
            lent_on = datetime.date.fromisoformat(lent_on_text)
        except ValueError:
            raise RejectedError("貸出日は YYYY-MM-DD で入力してください")
        if lent_on > today:
            raise RejectedError("未来の日付は指定できません")
    else:
        lent_on = today
    if repo.open_loan_of_item(item["code"]):
        raise RejectedError("この物は貸出中です")
    loans = repo.open_loans_of_employee(employee_no)
    if any(late_return(loan["due_on"], today) for loan in loans):
        raise RejectedError("返却の期限を過ぎた貸出があるため貸せません")
    if loans:
        raise RejectedError("同時に借りられるのは 1 件までです")
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    repo.insert_loan(item, employee_no, lent_on.isoformat(), due_on.isoformat())
    audit.record("parking_passes", "lend", item["code"])
    get_db().commit()


def return_item(item_code):
    item_code = _text(item_code)
    if repo.find_item(item_code) is None:
        raise RejectedError("物が見つかりません")
    loan = repo.open_loan_of_item(item_code)
    if loan is None:
        raise RejectedError("貸出中ではありません")
    repo.close_loan(loan["id"], clock.today().isoformat())
    audit.record("parking_passes", "return", item_code)
    get_db().commit()


def status_rows(q=""):
    """一覧と status.json に使う行。状態は free / lent / overdue。"""
    today = clock.today()
    return [
        {
            "code": r["code"],
            "name": r["name"],
            "status": item_status(r["due_on"], r["borrower"], today),
            "borrower": r["borrower"],
            "borrower_name": r["borrower_name"],
            "lent_on": r["lent_on"],
            "due_on": r["due_on"],
        }
        for r in repo.list_items(q)
    ]

"""ノート PC の貸出の判定と処理。受け付けないときは Rejected を投げる。"""

import datetime

from app.core import audit, clock
from app.core.db import get_db
from app.modules.laptops import repo

LOAN_DAYS = 14


class Rejected(Exception):
    """入力を受け付けない。メッセージは画面に出す理由。"""


def _need(value, label):
    value = (value or "").strip()
    if not value:
        raise Rejected(f"{label}を入力してください")
    return value


def create_item(code, name):
    code, name = _need(code, "番号"), _need(name, "名前")
    if repo.get_item(code):
        raise Rejected("この番号は既に登録されています")
    repo.insert_item(code, name)
    audit.record("laptops", "item_create", code)
    get_db().commit()


def update_item(code, name):
    code, name = _need(code, "番号"), _need(name, "名前")
    if repo.get_item(code) is None:
        raise Rejected("その番号の物はありません")
    repo.update_item(code, name)
    audit.record("laptops", "item_update", code)
    get_db().commit()


def delete_item(code):
    code = _need(code, "番号")
    if repo.get_item(code) is None:
        raise Rejected("その番号の物はありません")
    if repo.get_active_loan(code):
        raise Rejected("貸出中の物は削除できません")
    repo.delete_item(code)
    audit.record("laptops", "item_delete", code)
    get_db().commit()


def lend(item_code, employee_no, lent_on_text):
    """貸し出す。貸出の期間は 14 日。期限を過ぎた貸出を持つ社員には貸さない。"""
    today = clock.today()
    item = repo.get_item(_need(item_code, "物の番号"))
    if item is None:
        raise Rejected("その番号の物はありません")
    if repo.get_active_loan(item["code"]):
        raise Rejected("貸出中の物は貸せません")
    employee_no = _need(employee_no, "社員番号")
    if repo.get_borrowable_employee(employee_no) is None:
        raise Rejected("在籍している社員ではありません")
    text = (lent_on_text or "").strip()
    try:
        lent_on = datetime.date.fromisoformat(text) if text else today
    except ValueError:
        raise Rejected("貸出日は YYYY-MM-DD で入力してください")
    if lent_on > today:
        raise Rejected("貸出日に未来の日付は指定できません")
    if repo.count_loans_past_due(employee_no, today.isoformat()) > 0:
        raise Rejected("返却の期限を過ぎた貸出があるため、新しく貸せません")
    if repo.count_active_loans(employee_no) >= 1:
        raise Rejected("1 人が同時に借りられるのは 1 件までです")
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    repo.insert_loan(item, employee_no, lent_on.isoformat(), due_on.isoformat())
    audit.record("laptops", "lend", f"{item['code']}:{employee_no}")
    get_db().commit()


def give_back(item_code):
    item_code = _need(item_code, "物の番号")
    loan = repo.get_active_loan(item_code)
    if loan is None:
        raise Rejected("貸出中ではありません")
    repo.close_loan(loan["id"], clock.today().isoformat())
    audit.record("laptops", "return", item_code)
    get_db().commit()


def items(q=""):
    return repo.list_items((q or "").strip())


def history():
    return repo.list_history()


def status_items():
    return [dict(r) for r in repo.list_status(clock.today().isoformat())]

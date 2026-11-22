"""社用車の貸出の判定と処理。受け付けないときは ValueError（メッセージは画面に出す理由）。"""

import datetime

from app.core import audit, clock
from app.modules.vehicles import repo

LOAN_DAYS = 3  # 貸出の期間（日）


def _item_must_exist(code):
    if not code:
        raise ValueError("物の番号を入力してください")
    item = repo.find_item(code)
    if item is None:
        raise ValueError("その番号の物は登録されていません")
    return item


def create_item(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    if not code:
        raise ValueError("物の番号を入力してください")
    if not name:
        raise ValueError("名前を入力してください")
    if repo.find_item(code):
        raise ValueError("この番号は既に登録されています")
    repo.insert_item(code, name)
    audit.record("vehicles", "item_create", code)


def update_item(code, name):
    code, name = (code or "").strip(), (name or "").strip()
    _item_must_exist(code)
    if not name:
        raise ValueError("名前を入力してください")
    repo.update_item(code, name)
    audit.record("vehicles", "item_update", code)


def delete_item(code):
    code = (code or "").strip()
    _item_must_exist(code)
    if repo.find_open_loan(code):
        raise ValueError("貸出中の物は削除できません")
    repo.delete_item(code)
    audit.record("vehicles", "item_delete", code)


def lend(item_code, employee_no, lent_on_text):
    item_code, employee_no = (item_code or "").strip(), (employee_no or "").strip()
    today = clock.today()
    _item_must_exist(item_code)
    if repo.find_open_loan(item_code):
        raise ValueError("貸出中の物は貸せません")
    if repo.find_active_employee(employee_no) is None:
        raise ValueError("在籍している社員の番号を入力してください")
    lent_on_text = (lent_on_text or "").strip()
    if lent_on_text:
        try:
            lent_on = datetime.date.fromisoformat(lent_on_text)
        except ValueError:
            raise ValueError("貸出日は YYYY-MM-DD の形で入力してください")
    else:
        lent_on = today
    if lent_on > today:
        raise ValueError("貸出日に未来の日付は指定できません")
    # 返却の期限を過ぎたまま持っている社員には貸さない
    if repo.count_past_due_loans(employee_no, today.isoformat()) > 0:
        raise ValueError("返却の期限を過ぎた貸出があるため貸せません")
    if repo.count_open_loans(employee_no) >= 1:
        raise ValueError("1 人が同時に借りられるのは 1 件までです")
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    repo.insert_loan(item_code, employee_no, lent_on.isoformat(), due_on.isoformat())
    audit.record("vehicles", "lend", f"{item_code}:{employee_no}")


def return_item(item_code):
    item_code = (item_code or "").strip()
    _item_must_exist(item_code)
    loan = repo.find_open_loan(item_code)
    if loan is None:
        raise ValueError("貸出中ではありません")
    repo.close_loan(loan["id"], clock.today().isoformat())
    audit.record("vehicles", "return", f"{item_code}:{loan['employee_no']}")


def status_rows():
    return [
        {
            "code": r["code"],
            "name": r["name"],
            "status": r["status"],
            "borrower": r["borrower"],
            "lent_on": r["lent_on"],
            "due_on": r["due_on"],
        }
        for r in repo.list_status(clock.today().isoformat())
    ]


def items_for_screen(keyword):
    """一覧の画面用。状態は status_rows と同じ判定を使う。"""
    rows = {r["code"]: r for r in status_rows()}
    return [rows[i["code"]] for i in repo.list_items(keyword)]

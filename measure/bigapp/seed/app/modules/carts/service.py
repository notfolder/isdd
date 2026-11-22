"""台車の貸出の判定と処理。"""

import datetime

from app.core import audit, clock
from app.core.db import get_db
from app.modules.carts import repo

LOAN_DAYS = 1  # 貸出の期間（日）
MAX_LOANS = 2  # 1 人が同時に借りられる数


class Rejected(Exception):
    """受け付けない入力。メッセージは画面に出す理由。"""


def _commit():
    get_db().commit()


def create_item(code, name):
    code, name = code.strip(), name.strip()
    if not code or not name:
        raise Rejected("番号と名前を入力してください")
    if repo.get_item(code):
        raise Rejected("この番号は既に登録されています")
    repo.insert_item(code, name)
    audit.record("carts", "item_create", code)
    _commit()


def update_item(code, name):
    code, name = code.strip(), name.strip()
    if not name:
        raise Rejected("名前を入力してください")
    if repo.get_item(code) is None:
        raise Rejected("物が見つかりません")
    repo.update_item(code, name)
    audit.record("carts", "item_update", code)
    _commit()


def delete_item(code):
    code = code.strip()
    if repo.get_item(code) is None:
        raise Rejected("物が見つかりません")
    if repo.current_loan_of_item(code):
        raise Rejected("貸出中の物は削除できません")
    repo.delete_item(code)
    audit.record("carts", "item_delete", code)
    _commit()


def check_lendable(item_code, employee_no, lent_on_text):
    """貸出の入力のうち、期限の比較以外の判定。貸せるなら (貸出日, 期限) を返す。"""
    if repo.get_item(item_code) is None:
        raise Rejected("物が見つかりません")
    if repo.current_loan_of_item(item_code):
        raise Rejected("貸出中の物は貸せません")
    if repo.find_active_employee(employee_no) is None:
        raise Rejected("在籍している社員を指定してください")
    if lent_on_text:
        try:
            lent_on = datetime.date.fromisoformat(lent_on_text)
        except ValueError:
            raise Rejected("貸出日は YYYY-MM-DD で入力してください")
    else:
        lent_on = clock.today()
    if lent_on > clock.today():
        raise Rejected("未来の日付は指定できません")
    return lent_on, lent_on + datetime.timedelta(days=LOAN_DAYS)


def check_limit(employee_no):
    if len(repo.open_loans_of_employee(employee_no)) >= MAX_LOANS:
        raise Rejected(f"1 人が同時に借りられるのは {MAX_LOANS} 件までです")


def register_loan(item_code, employee_no, lent_on, due_on):
    repo.insert_loan(item_code, employee_no, lent_on.isoformat(), due_on.isoformat())
    audit.record("carts", "lend", item_code)
    _commit()


def return_item(item_code):
    item_code = item_code.strip()
    loan = repo.current_loan_of_item(item_code)
    if loan is None:
        raise Rejected("貸出中ではありません")
    repo.close_loan(loan["id"], clock.today().isoformat())
    audit.record("carts", "return", item_code)
    _commit()


def status_of(row):
    """物の状態 free / lent / overdue（status.json 用。今日 > 期限なら overdue）。"""
    if row["borrower"] is None:
        return "free"
    if clock.today() > datetime.date.fromisoformat(row["due_on"]):
        return "overdue"
    return "lent"


def status_list(q=""):
    """一覧と status.json の元になる、物ごとの状態。"""
    return [dict(r, status=status_of(r)) for r in repo.list_items(q)]

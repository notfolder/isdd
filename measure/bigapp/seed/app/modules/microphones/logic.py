"""マイクの貸出の処理。画面（__init__.py）から呼ばれ、判定と DB の読み書きをここに集める。"""

import datetime
import sqlite3
from dataclasses import dataclass
from typing import Optional

from app.core import clock

LOAN_DAYS = 3  # 貸出の期間（日）。返却の期限 = 貸出日 + 3 日
MAX_LOANS = 3  # 1 人が同時に借りられる件数
EXCLUDED_STATUSES = {"retired"}  # 貸出の対象にしない社員の状態


class RuleError(Exception):
    """きまりに合わず受け付けないとき。メッセージはそのまま画面に出す。"""


@dataclass
class Item:
    """マイク 1 本と、今の貸出の状態。"""

    code: str
    name: str
    borrower: Optional[str] = None
    borrower_name: Optional[str] = None
    lent_on: Optional[str] = None
    due_on: Optional[str] = None

    @property
    def status(self) -> str:
        if self.borrower is None:
            return "free"
        if self.due_on is not None and clock.today() > datetime.date.fromisoformat(self.due_on):
            return "overdue"
        return "lent"

    def as_json(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "borrower": self.borrower,
            "lent_on": self.lent_on,
            "due_on": self.due_on,
        }


@dataclass
class Loan:
    """過去の貸出 1 件。"""

    item_code: str
    item_name: str
    employee_no: str
    employee_name: str
    lent_on: str
    due_on: str
    returned_on: str


def list_items(db: sqlite3.Connection, q: str = "") -> list:
    """物の一覧（番号の昇順）。q があれば番号か名前の一部で絞り込む。"""
    rows = db.execute(
        "SELECT i.code, i.name, l.employee_no, e.name AS employee_name, l.lent_on, l.due_on "
        "FROM microphones_items i "
        "LEFT JOIN microphones_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "ORDER BY i.code"
    ).fetchall()
    items = [Item(r["code"], r["name"], r["employee_no"], r["employee_name"], r["lent_on"], r["due_on"]) for r in rows]
    q = q.strip()
    if q:
        items = [i for i in items if q in i.code or q in i.name]
    return items


def list_history(db: sqlite3.Connection) -> list:
    """返却済みの貸出（新しい順）。"""
    rows = db.execute(
        "SELECT l.*, i.name AS item_name, e.name AS employee_name FROM microphones_loans l "
        "LEFT JOIN microphones_items i ON i.code = l.item_code "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()
    return [Loan(r["item_code"], r["item_name"] or r["item_code"], r["employee_no"], r["employee_name"] or "", r["lent_on"], r["due_on"], r["returned_on"]) for r in rows]


def _get_item(db, code: str):
    return db.execute("SELECT * FROM microphones_items WHERE code = ?", (code,)).fetchone()


def _is_lent(db, code: str) -> bool:
    return db.execute("SELECT 1 FROM microphones_loans WHERE item_code = ? AND returned_on IS NULL", (code,)).fetchone() is not None


def create_item(db, code: str, name: str) -> str:
    code, name = code.strip(), name.strip()
    if not code:
        raise RuleError("番号を入力してください")
    if not name:
        raise RuleError("名前を入力してください")
    if _get_item(db, code):
        raise RuleError("この番号は既に登録されています")
    db.execute("INSERT INTO microphones_items (code, name) VALUES (?, ?)", (code, name))
    return code


def update_item(db, code: str, name: str) -> str:
    code, name = code.strip(), name.strip()
    if not name:
        raise RuleError("名前を入力してください")
    if _get_item(db, code) is None:
        raise RuleError("物が見つかりません")
    db.execute("UPDATE microphones_items SET name = ? WHERE code = ?", (name, code))
    return code


def delete_item(db, code: str) -> str:
    code = code.strip()
    if _get_item(db, code) is None:
        raise RuleError("物が見つかりません")
    if _is_lent(db, code):
        raise RuleError("貸出中の物は削除できません")
    db.execute("DELETE FROM microphones_items WHERE code = ?", (code,))
    return code


def lend(db, item_code: str, employee_no: str, lent_on_text: str) -> str:
    """貸し出す。きまりに合わなければ RuleError。"""
    item_code, employee_no = item_code.strip(), employee_no.strip()
    today = clock.today()
    lent_on_text = (lent_on_text or "").strip()
    if lent_on_text:
        try:
            lent_on = datetime.date.fromisoformat(lent_on_text)
        except ValueError:
            raise RuleError("貸出日は YYYY-MM-DD の形で入力してください")
        if len(lent_on_text) != 10:
            raise RuleError("貸出日は YYYY-MM-DD の形で入力してください")
    else:
        lent_on = today
    if lent_on > today:
        raise RuleError("未来の日付は貸出日にできません")
    if _get_item(db, item_code) is None:
        raise RuleError("物が見つかりません")
    employee = db.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise RuleError("社員が見つかりません")
    if employee["status"] in EXCLUDED_STATUSES:
        raise RuleError("退職した社員には貸し出せません")
    if _is_lent(db, item_code):
        raise RuleError("貸出中の物は貸せません")

    held = db.execute("SELECT due_on FROM microphones_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)).fetchall()
    if len(held) >= MAX_LOANS:
        raise RuleError("同時に借りられるのは %d 件までです" % MAX_LOANS)
    due_dates = [datetime.date.fromisoformat(r["due_on"]) for r in held]
    past_due = any(due < today for due in due_dates)
    if past_due:
        raise RuleError("返却の期限を過ぎた貸出があるため、新しく貸せません")

    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    db.execute(
        "INSERT INTO microphones_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item_code, employee_no, lent_on.isoformat(), due_on.isoformat()),
    )
    return item_code


def give_back(db, item_code: str) -> str:
    item_code = item_code.strip()
    if _get_item(db, item_code) is None:
        raise RuleError("物が見つかりません")
    if not _is_lent(db, item_code):
        raise RuleError("貸出中ではありません")
    db.execute(
        "UPDATE microphones_loans SET returned_on = ? WHERE item_code = ? AND returned_on IS NULL",
        (clock.today().isoformat(), item_code),
    )
    return item_code

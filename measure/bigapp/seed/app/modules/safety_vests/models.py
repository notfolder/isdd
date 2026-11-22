"""安全ベストの貸出の判定とデータの読み書き。"""

import datetime

from app.core import clock
from app.core.db import get_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS safety_vests_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS safety_vests_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

LOAN_DAYS = 14  # 貸出の期間（日）
MAX_LOANS = 2  # 1 人が同時に借りられる件数


class RuleError(Exception):
    """きまりに反するため受け付けない（理由を画面に出す）。"""


def is_retired(employee) -> bool:
    """退職した社員か。"""
    return employee["status"] == "retired"


def has_overdue_loan(employee_no: str) -> bool:
    """返却の期限を過ぎた（今日 > 期限）貸出を持っているか。"""
    row = get_db().execute(
        "SELECT 1 FROM safety_vests_loans WHERE employee_no = ? AND returned_on IS NULL AND due_on < ? LIMIT 1",
        (employee_no, clock.today().isoformat()),
    ).fetchone()
    return row is not None


class VestLoans:
    """物の登録と貸出のきまりをまとめたクラス。"""

    # --- 読み取り ---
    def get_item(self, code):
        return get_db().execute("SELECT * FROM safety_vests_items WHERE code = ?", (code,)).fetchone()

    def open_loan(self, code):
        """返却されていない貸出（無ければ None）。"""
        return get_db().execute(
            "SELECT * FROM safety_vests_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
        ).fetchone()

    def count_open_loans(self, employee_no) -> int:
        return get_db().execute(
            "SELECT COUNT(*) FROM safety_vests_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
        ).fetchone()[0]

    def status_of(self, loan) -> str:
        if loan is None:
            return "free"
        return "overdue" if clock.today().isoformat() > loan["due_on"] else "lent"

    def list_items(self, q=""):
        """物の一覧（状態・借りている社員つき、code の昇順）。"""
        rows = get_db().execute(
            "SELECT i.code, i.name, l.employee_no, l.lent_on, l.due_on, e.name AS borrower_name "
            "FROM safety_vests_items i "
            "LEFT JOIN safety_vests_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
            "LEFT JOIN employees e ON e.employee_no = l.employee_no ORDER BY i.code"
        ).fetchall()
        q = (q or "").strip()
        result = []
        for r in rows:
            if q and q not in r["code"] and q not in r["name"]:
                continue
            loan = {"due_on": r["due_on"]} if r["employee_no"] else None
            result.append({
                "code": r["code"], "name": r["name"], "status": self.status_of(loan),
                "borrower": r["employee_no"], "borrower_name": r["borrower_name"],
                "lent_on": r["lent_on"], "due_on": r["due_on"],
            })
        return result

    def history(self):
        """返却済みの貸出（新しい順）。"""
        return get_db().execute(
            "SELECT l.*, e.name AS borrower_name FROM safety_vests_loans l "
            "LEFT JOIN employees e ON e.employee_no = l.employee_no "
            "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
        ).fetchall()

    # --- 物の登録 ---
    def create_item(self, code, name):
        code, name = (code or "").strip(), (name or "").strip()
        if not code:
            raise RuleError("番号を入力してください")
        if not name:
            raise RuleError("名前を入力してください")
        if self.get_item(code):
            raise RuleError("この番号は既に登録されています")
        get_db().execute("INSERT INTO safety_vests_items (code, name) VALUES (?, ?)", (code, name))
        return code

    def update_item(self, code, name):
        code, name = (code or "").strip(), (name or "").strip()
        if not self.get_item(code):
            raise RuleError("物が見つかりません")
        if not name:
            raise RuleError("名前を入力してください")
        get_db().execute("UPDATE safety_vests_items SET name = ? WHERE code = ?", (name, code))
        return code

    def delete_item(self, code):
        code = (code or "").strip()
        if not self.get_item(code):
            raise RuleError("物が見つかりません")
        if self.open_loan(code):
            raise RuleError("貸出中の物は削除できません")
        get_db().execute("DELETE FROM safety_vests_items WHERE code = ?", (code,))
        return code

    # --- 貸出と返却 ---
    def lend(self, code, employee_no, lent_on_text):
        code, employee_no = (code or "").strip(), (employee_no or "").strip()
        if not self.get_item(code):
            raise RuleError("物が見つかりません")
        employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
        if employee is None or is_retired(employee):
            raise RuleError("在籍している社員を指定してください")
        today = clock.today()
        text = (lent_on_text or "").strip()
        if text:
            try:
                lent_on = datetime.date.fromisoformat(text)
            except ValueError:
                raise RuleError("貸出日は YYYY-MM-DD で入力してください")
            if lent_on > today:
                raise RuleError("未来の日付は指定できません")
        else:
            lent_on = today
        if self.open_loan(code):
            raise RuleError("この物は貸出中です")
        if has_overdue_loan(employee_no):
            raise RuleError("返却の期限を過ぎた貸出があるため貸せません")
        if self.count_open_loans(employee_no) >= MAX_LOANS:
            raise RuleError(f"同時に借りられるのは {MAX_LOANS} 件までです")
        due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
        get_db().execute(
            "INSERT INTO safety_vests_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
            (code, employee_no, lent_on.isoformat(), due_on.isoformat()),
        )
        return code

    def return_item(self, code):
        code = (code or "").strip()
        if not self.get_item(code):
            raise RuleError("物が見つかりません")
        loan = self.open_loan(code)
        if loan is None:
            raise RuleError("この物は貸出中ではありません")
        get_db().execute(
            "UPDATE safety_vests_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"])
        )
        return code

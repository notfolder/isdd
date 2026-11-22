"""テントの貸出の判定とデータ操作。ルールはすべてこのクラスにまとめる。"""

import datetime

from app.core import clock
from app.core.db import get_db

LOAN_DAYS = 4  # 貸出の期間（日）


class LendingError(Exception):
    """受け付けない理由を画面に出すための例外。"""


def is_retired(employee) -> bool:
    """退職した社員なら True。"""
    return employee["status"] == "retired"


class TentLending:
    """テントの台帳と貸出の判定。"""

    # ---- 物の台帳 ----
    def items(self, query=""):
        """物の一覧（番号の昇順）。貸出中ならその貸出の情報を付ける。"""
        rows = get_db().execute(
            "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on "
            "FROM tents_items i LEFT JOIN tents_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
            "ORDER BY i.code"
        ).fetchall()
        result = []
        for r in rows:
            if query and query not in r["code"] and query not in r["name"]:
                continue
            result.append({**dict(r), "status": self._status(r["due_on"])})
        return result

    def _status(self, due_on):
        if due_on is None:
            return "free"
        if self.is_delinquent_due(due_on):
            return "overdue"
        return "lent"

    @staticmethod
    def is_delinquent_due(due_on) -> bool:
        """期限を過ぎている（今日 > 期限）なら延滞。"""
        return clock.today() > datetime.date.fromisoformat(due_on)

    def _item(self, code):
        return get_db().execute("SELECT * FROM tents_items WHERE code = ?", (code,)).fetchone()

    def _active_loan_of_item(self, code):
        return get_db().execute("SELECT * FROM tents_loans WHERE item_code = ? AND returned_on IS NULL", (code,)).fetchone()

    def create_item(self, code, name):
        code, name = (code or "").strip(), (name or "").strip()
        if not code:
            raise LendingError("番号を入力してください")
        if not name:
            raise LendingError("名前を入力してください")
        if self._item(code):
            raise LendingError("この番号は既に登録されています")
        get_db().execute("INSERT INTO tents_items (code, name) VALUES (?, ?)", (code, name))
        return code

    def update_item(self, code, name):
        code, name = (code or "").strip(), (name or "").strip()
        if not self._item(code):
            raise LendingError("物が見つかりません")
        if not name:
            raise LendingError("名前を入力してください")
        get_db().execute("UPDATE tents_items SET name = ? WHERE code = ?", (name, code))
        return code

    def delete_item(self, code):
        code = (code or "").strip()
        if not self._item(code):
            raise LendingError("物が見つかりません")
        if self._active_loan_of_item(code):
            raise LendingError("貸出中の物は削除できません")
        get_db().execute("DELETE FROM tents_items WHERE code = ?", (code,))
        return code

    # ---- 貸出・返却 ----
    def has_delinquent_loan(self, employee_no) -> bool:
        """この社員が期限を過ぎた貸出を持っているか。"""
        rows = get_db().execute(
            "SELECT due_on FROM tents_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
        ).fetchall()
        return any(self.is_delinquent_due(r["due_on"]) for r in rows)

    def lend(self, item_code, employee_no, lent_on_text):
        item_code, employee_no = (item_code or "").strip(), (employee_no or "").strip()
        item = self._item(item_code)
        if not item:
            raise LendingError("物が見つかりません")
        employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
        if employee is None:
            raise LendingError("社員が見つかりません")
        if not (not is_retired(employee)):
            raise LendingError("退職した社員には貸し出せません")
        today = clock.today()
        lent_on_text = (lent_on_text or "").strip()
        if lent_on_text:
            try:
                lent_on = datetime.date.fromisoformat(lent_on_text)
            except ValueError:
                raise LendingError("貸出日は YYYY-MM-DD で入力してください")
            if lent_on > today:
                raise LendingError("未来の日付は指定できません")
        else:
            lent_on = today
        if self._active_loan_of_item(item_code):
            raise LendingError("この物は貸出中です")
        if self.has_delinquent_loan(employee_no):
            raise LendingError("返却の期限を過ぎた貸出があるため、貸し出せません")
        held = get_db().execute(
            "SELECT COUNT(*) FROM tents_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
        ).fetchone()[0]
        if held >= 1:
            raise LendingError("1 人が同時に借りられるのは 1 件までです")
        due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
        get_db().execute(
            "INSERT INTO tents_loans (item_code, item_name, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?, ?)",
            (item_code, item["name"], employee_no, lent_on.isoformat(), due_on.isoformat()),
        )
        return item_code

    def give_back(self, item_code):
        item_code = (item_code or "").strip()
        if not self._item(item_code):
            raise LendingError("物が見つかりません")
        loan = self._active_loan_of_item(item_code)
        if not loan:
            raise LendingError("この物は貸出中ではありません")
        get_db().execute("UPDATE tents_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
        return item_code

    def history(self):
        """返却済みの貸出（新しい順）。"""
        return get_db().execute(
            "SELECT * FROM tents_loans WHERE returned_on IS NOT NULL ORDER BY lent_on DESC, id DESC"
        ).fetchall()

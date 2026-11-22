"""書籍の貸出の判定。貸せるか、延滞しているか、といった業務のきまりをここにまとめる。"""

import datetime

from app.core import clock
from app.core.db import get_db

LOAN_DAYS = 21  # 貸出の期間（日）
MAX_LOANS = 3  # 1 人が同時に借りられる件数


class RuleError(Exception):
    """きまりに合わないため受け付けられない。メッセージは画面にそのまま出す。"""


class BookRules:
    """書籍の登録・貸出・返却のきまりを判定し、データを読み書きする。commit は呼び出し側で行う。"""

    # ---- 読み取り ----

    def find_item(self, code):
        return get_db().execute("SELECT code, name FROM books_items WHERE code = ?", (code,)).fetchone()

    def open_loan(self, code):
        """貸出中（未返却）の記録。無ければ None。"""
        return get_db().execute(
            "SELECT * FROM books_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
        ).fetchone()

    def find_active_employee(self, employee_no):
        """在籍している社員だけを返す。退職者と存在しない番号は None。"""
        return get_db().execute(
            "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'",
            (employee_no,),
        ).fetchone()

    def is_delinquent(self, due_on, today=None):
        """返却の期限を過ぎているか（今日 > 期限）。期限当日は延滞ではない。"""
        today = today or clock.today()
        return today > datetime.date.fromisoformat(due_on)

    def has_delinquent_loan(self, employee_no):
        today = clock.today()
        rows = get_db().execute(
            "SELECT due_on FROM books_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
        ).fetchall()
        return any(self.is_delinquent(r["due_on"], today) for r in rows)

    def count_open_loans(self, employee_no):
        return get_db().execute(
            "SELECT COUNT(*) FROM books_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
        ).fetchone()[0]

    def status_of(self, loan):
        """free / lent / overdue。status.json に出す値は契約どおり overdue とする。"""
        if loan is None:
            return "free"
        return "overdue" if self.is_delinquent(loan["due_on"]) else "lent"

    def list_items(self, q=""):
        """一覧の行（物ごとに、貸出中ならその記録を付ける）。code の昇順。"""
        sql = (
            "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, e.name AS borrower_name "
            "FROM books_items i "
            "LEFT JOIN books_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
            "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        )
        args = ()
        if q:
            like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            sql += "WHERE i.code LIKE ? ESCAPE '\\' OR i.name LIKE ? ESCAPE '\\' "
            args = (like, like)
        sql += "ORDER BY i.code"
        rows = []
        for r in get_db().execute(sql, args).fetchall():
            row = dict(r)
            row["status"] = "free" if r["borrower"] is None else ("overdue" if self.is_delinquent(r["due_on"]) else "lent")
            rows.append(row)
        return rows

    def list_history(self):
        """返却済みの貸出。新しい順。"""
        return get_db().execute(
            "SELECT l.*, i.name AS item_name, e.name AS borrower_name FROM books_loans l "
            "LEFT JOIN books_items i ON i.code = l.item_code "
            "LEFT JOIN employees e ON e.employee_no = l.employee_no "
            "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
        ).fetchall()

    # ---- 書き込み（きまりの判定つき） ----

    def create_item(self, code, name):
        if not code:
            raise RuleError("番号を入力してください")
        if not name:
            raise RuleError("名前を入力してください")
        if self.find_item(code):
            raise RuleError("この番号は既に登録されています")
        get_db().execute("INSERT INTO books_items (code, name) VALUES (?, ?)", (code, name))

    def update_item(self, code, name):
        if self.find_item(code) is None:
            raise RuleError("該当する書籍が見つかりません")
        if not name:
            raise RuleError("名前を入力してください")
        get_db().execute("UPDATE books_items SET name = ? WHERE code = ?", (name, code))

    def delete_item(self, code):
        if self.find_item(code) is None:
            raise RuleError("該当する書籍が見つかりません")
        if self.open_loan(code):
            raise RuleError("貸出中の書籍は削除できません")
        get_db().execute("DELETE FROM books_items WHERE code = ?", (code,))
        # 履歴は残す

    def lend(self, item_code, employee_no, lent_on_text):
        if self.find_item(item_code) is None:
            raise RuleError("該当する書籍が見つかりません")
        if self.open_loan(item_code):
            raise RuleError("この書籍は貸出中です")
        if self.find_active_employee(employee_no) is None:
            raise RuleError("在籍している社員を指定してください")
        today = clock.today()
        if lent_on_text:
            try:
                lent_on = datetime.date.fromisoformat(lent_on_text)
            except ValueError:
                raise RuleError("貸出日は YYYY-MM-DD の形で入力してください")
            if lent_on > today:
                raise RuleError("貸出日に未来の日付は指定できません")
        else:
            lent_on = today
        if self.has_delinquent_loan(employee_no):
            raise RuleError("返却期限を過ぎた貸出があるため、新しく貸し出せません")
        if self.count_open_loans(employee_no) >= MAX_LOANS:
            raise RuleError(f"同時に借りられるのは {MAX_LOANS} 件までです")
        due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
        get_db().execute(
            "INSERT INTO books_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
            (item_code, employee_no, lent_on.isoformat(), due_on.isoformat()),
        )

    def give_back(self, item_code):
        if self.find_item(item_code) is None:
            raise RuleError("該当する書籍が見つかりません")
        loan = self.open_loan(item_code)
        if loan is None:
            raise RuleError("この書籍は貸出中ではありません")
        get_db().execute("UPDATE books_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))

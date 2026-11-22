"""カメラ貸出の判定をまとめたクラス。DB の読み書きと、貸せるかどうかの判断を持つ。"""

import datetime

from app.core import clock
from app.core.db import get_db

LOAN_DAYS = 5  # 貸出の期間（日）
MAX_PER_PERSON = 1  # 1 人が同時に借りられる件数


class CameraError(Exception):
    """受け付けない理由。メッセージをそのまま画面に出す。"""


class CameraRules:
    """物・貸出の読み取りと、各操作の判定。判定に通らなければ CameraError を投げる。"""

    # ---- 読み取り ----
    def items(self, q=""):
        """物の一覧（番号の昇順）。貸出中ならその貸出の情報を付ける。"""
        sql = (
            "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on "
            "FROM cameras_items i LEFT JOIN cameras_loans l ON l.item_code = i.code AND l.returned_on IS NULL"
        )
        params = []
        if q:
            sql += " WHERE i.code LIKE ? OR i.name LIKE ?"
            params = [f"%{q}%", f"%{q}%"]
        rows = get_db().execute(sql + " ORDER BY i.code", params).fetchall()
        today = clock.today()
        result = []
        for r in rows:
            if r["borrower"] is None:
                status = "free"
            elif today > datetime.date.fromisoformat(r["due_on"]):
                status = "overdue"
            else:
                status = "lent"
            result.append({
                "code": r["code"], "name": r["name"], "status": status,
                "borrower": r["borrower"], "lent_on": r["lent_on"], "due_on": r["due_on"],
            })
        return result

    def history(self):
        """返却済みの貸出（新しい順）。"""
        return get_db().execute(
            "SELECT l.item_code, i.name AS item_name, l.employee_no, e.name AS employee_name, "
            "l.lent_on, l.due_on, l.returned_on "
            "FROM cameras_loans l LEFT JOIN cameras_items i ON i.code = l.item_code "
            "LEFT JOIN employees e ON e.employee_no = l.employee_no "
            "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
        ).fetchall()

    def _item(self, code):
        return get_db().execute("SELECT * FROM cameras_items WHERE code = ?", (code,)).fetchone()

    def _open_loan(self, code):
        return get_db().execute(
            "SELECT * FROM cameras_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
        ).fetchone()

    def _active_employee(self, number):
        """在籍している社員の行。退職者と存在しない番号は None。"""
        return get_db().execute(
            "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'", (number,)
        ).fetchone()

    def _past_due(self, employee_no):
        """この社員が借りている貸出の返却期限を並べ、期限切れがあるかを調べる。"""
        due_dates = [
            datetime.date.fromisoformat(r["due_on"])
            for r in get_db().execute(
                "SELECT due_on FROM cameras_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
            ).fetchall()
        ]
        today = clock.today()
        return any(today > d for d in due_dates)

    # ---- 物の操作 ----
    def create_item(self, code, name):
        code, name = (code or "").strip(), (name or "").strip()
        if not code:
            raise CameraError("番号を入力してください")
        if not name:
            raise CameraError("名前を入力してください")
        if self._item(code):
            raise CameraError("この番号は既に登録されています")
        get_db().execute("INSERT INTO cameras_items (code, name) VALUES (?, ?)", (code, name))
        return code

    def update_item(self, code, name):
        code, name = (code or "").strip(), (name or "").strip()
        if not name:
            raise CameraError("名前を入力してください")
        if not self._item(code):
            raise CameraError("その物は登録されていません")
        get_db().execute("UPDATE cameras_items SET name = ? WHERE code = ?", (name, code))
        return code

    def delete_item(self, code):
        code = (code or "").strip()
        if not self._item(code):
            raise CameraError("その物は登録されていません")
        if self._open_loan(code):
            raise CameraError("貸出中の物は削除できません")
        get_db().execute("DELETE FROM cameras_items WHERE code = ?", (code,))
        return code

    # ---- 貸出・返却 ----
    def lend(self, item_code, employee_no, lent_on_text):
        item_code, employee_no = (item_code or "").strip(), (employee_no or "").strip()
        today = clock.today()
        if lent_on_text and lent_on_text.strip():
            try:
                lent_on = datetime.date.fromisoformat(lent_on_text.strip())
            except ValueError:
                raise CameraError("貸出日は YYYY-MM-DD の形で入力してください")
            if lent_on > today:
                raise CameraError("貸出日に未来の日付は指定できません")
        else:
            lent_on = today
        if not self._item(item_code):
            raise CameraError("その物は登録されていません")
        if not self._active_employee(employee_no):
            raise CameraError("在籍している社員を指定してください")
        if self._open_loan(item_code):
            raise CameraError("この物は貸出中です")
        if self._past_due(employee_no):
            raise CameraError("返却の期限を過ぎた貸出があるため、貸せません")
        held = get_db().execute(
            "SELECT COUNT(*) FROM cameras_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
        ).fetchone()[0]
        if held >= MAX_PER_PERSON:
            raise CameraError("1 人が同時に借りられるのは 1 件までです")
        due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
        get_db().execute(
            "INSERT INTO cameras_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
            (item_code, employee_no, lent_on.isoformat(), due_on.isoformat()),
        )
        return item_code

    def give_back(self, item_code):
        item_code = (item_code or "").strip()
        loan = self._open_loan(item_code)
        if not loan:
            raise CameraError("この物は貸出中ではありません")
        get_db().execute("UPDATE cameras_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
        return item_code

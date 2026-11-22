"""ヘルメット貸出の判定と DB 操作。受け付けられないときは HelmetError を投げる。"""

import datetime

from app.core import clock
from app.core.db import get_db

LOAN_DAYS = 10  # 貸出の期間（日）
MAX_LOANS = 2  # 1 人が同時に借りられる件数


class HelmetError(Exception):
    """受け付けない理由（画面にそのまま出す）。"""


def _clean(value):
    return (value or "").strip()


def get_item(code):
    return get_db().execute("SELECT * FROM helmets_items WHERE code = ?", (code,)).fetchone()


def _require_item(code):
    item = get_item(code)
    if item is None:
        raise HelmetError("そのヘルメットは登録されていません")
    return item


def open_loan(code):
    """貸出中の記録。無ければ None。"""
    return get_db().execute(
        "SELECT * FROM helmets_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def create_item(code, name):
    code, name = _clean(code), _clean(name)
    if not code:
        raise HelmetError("番号を入力してください")
    if not name:
        raise HelmetError("名前を入力してください")
    if get_item(code):
        raise HelmetError("この番号は既に登録されています")
    get_db().execute("INSERT INTO helmets_items (code, name) VALUES (?, ?)", (code, name))
    return code


def update_item(code, name):
    code, name = _clean(code), _clean(name)
    _require_item(code)
    if not name:
        raise HelmetError("名前を入力してください")
    get_db().execute("UPDATE helmets_items SET name = ? WHERE code = ?", (name, code))
    return code


def delete_item(code):
    code = _clean(code)
    _require_item(code)
    if open_loan(code):
        raise HelmetError("貸出中のヘルメットは削除できません")
    get_db().execute("DELETE FROM helmets_items WHERE code = ?", (code,))
    return code


def _parse_date(text):
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise HelmetError("貸出日は YYYY-MM-DD の形で入力してください")


def expired_loans(employee_no):
    """返却の期限を過ぎている（今日 > 期限）貸出中の記録。"""
    today = clock.today().isoformat()
    return get_db().execute(
        "SELECT * FROM helmets_loans WHERE employee_no = ? AND returned_on IS NULL AND due_on < ?",
        (employee_no, today),
    ).fetchall()


def lend(item_code, employee_no, lent_on_text):
    item_code, employee_no = _clean(item_code), _clean(employee_no)
    db = get_db()
    employee = db.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise HelmetError("その社員は存在しません")
    if employee["status"] != "active":
        raise HelmetError("退職した社員には貸し出せません")
    _require_item(item_code)
    if open_loan(item_code):
        raise HelmetError("このヘルメットは貸出中です")
    today = clock.today()
    lent_on_text = _clean(lent_on_text)
    lent_on = _parse_date(lent_on_text) if lent_on_text else today
    if lent_on > today:
        raise HelmetError("貸出日に未来の日付は指定できません")
    if expired_loans(employee_no):
        raise HelmetError("返却の期限を過ぎた貸出があるため、新しく貸し出せません")
    count = db.execute(
        "SELECT COUNT(*) FROM helmets_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchone()[0]
    if count >= MAX_LOANS:
        raise HelmetError("同時に借りられるのは %d 件までです" % MAX_LOANS)
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    db.execute(
        "INSERT INTO helmets_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item_code, employee_no, lent_on.isoformat(), due_on.isoformat()),
    )
    return item_code


def return_item(item_code):
    item_code = _clean(item_code)
    _require_item(item_code)
    loan = open_loan(item_code)
    if loan is None:
        raise HelmetError("このヘルメットは貸出中ではありません")
    get_db().execute("UPDATE helmets_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
    return item_code


def list_items(q=""):
    """物の一覧（状態つき）。q は番号か名前の一部。"""
    today = clock.today().isoformat()
    rows = get_db().execute(
        "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, e.name AS borrower_name "
        "FROM helmets_items i LEFT JOIN helmets_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no ORDER BY i.code"
    ).fetchall()
    q = _clean(q).lower()
    result = []
    for r in rows:
        if q and q not in r["code"].lower() and q not in r["name"].lower():
            continue
        item = dict(r)
        if r["borrower"] is None:
            item["status"] = "free"
        elif r["due_on"] < today:
            item["status"] = "overdue"
        else:
            item["status"] = "lent"
        result.append(item)
    return result


def list_history():
    """返却済みの貸出（新しい順）。"""
    return get_db().execute(
        "SELECT l.*, i.name AS item_name, e.name AS borrower_name FROM helmets_loans l "
        "LEFT JOIN helmets_items i ON i.code = l.item_code LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()

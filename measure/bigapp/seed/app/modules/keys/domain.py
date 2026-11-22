"""鍵の貸出の判定。受け付けないときは RejectedError を投げ、画面側で 400 にする。"""

import datetime

from app.core import clock
from app.core.db import get_db

LOAN_DAYS = 1  # 貸出の期間（日）。返却の期限 = 貸出日 + LOAN_DAYS
MAX_LOANS_PER_PERSON = 2  # 1 人が同時に借りられる件数
EXCLUDED_STATUSES = {"retired"}  # 貸出の対象にできない社員の状態

# 貸出の行を読むときに、延滞かどうかを state の列として作る（今日 > 期限 なら overdue）。
LOAN_STATE_SQL = """
CASE
    WHEN returned_on IS NOT NULL THEN 'returned'
    WHEN :today > due_on THEN 'overdue'
    ELSE 'lent'
END AS state
"""


class RejectedError(Exception):
    """入力を受け付けない。メッセージが画面に出る理由。"""


def _today_text():
    return clock.today().isoformat()


def _need(value, label):
    value = (value or "").strip()
    if not value:
        raise RejectedError(f"{label}を入力してください")
    return value


def _get_item(code):
    return get_db().execute("SELECT * FROM keys_items WHERE code = ?", (code,)).fetchone()


def _open_loans(where="1=1", params=()):
    """返却されていない貸出の行（state つき）。"""
    sql = f"SELECT *, {LOAN_STATE_SQL} FROM keys_loans WHERE returned_on IS NULL AND {where}"
    return get_db().execute(sql, {"today": _today_text(), **dict(params)}).fetchall()


def _require_item(code):
    code = _need(code, "物の番号")
    item = _get_item(code)
    if item is None:
        raise RejectedError("その番号の物は登録されていません")
    return item


def create_item(code, name):
    code, name = _need(code, "物の番号"), _need(name, "名前")
    if _get_item(code):
        raise RejectedError("この番号は既に登録されています")
    get_db().execute("INSERT INTO keys_items (code, name) VALUES (?, ?)", (code, name))
    return code


def update_item(code, name):
    item = _require_item(code)
    name = _need(name, "名前")
    get_db().execute("UPDATE keys_items SET name = ? WHERE code = ?", (name, item["code"]))
    return item["code"]


def delete_item(code):
    item = _require_item(code)
    if _open_loans("item_code = :c", {"c": item["code"]}):
        raise RejectedError("貸出中の物は削除できません")
    get_db().execute("DELETE FROM keys_items WHERE code = ?", (item["code"],))
    return item["code"]


def _parse_date(text):
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise RejectedError("貸出日は YYYY-MM-DD の形で入力してください")


def lend(item_code, employee_no, lent_on_text):
    item = _require_item(item_code)
    employee_no = _need(employee_no, "社員番号")
    employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise RejectedError("その社員番号の社員は居ません")
    if employee["status"] in EXCLUDED_STATUSES:
        raise RejectedError("退職した社員には貸し出せません")

    lent_on_text = (lent_on_text or "").strip()
    lent_on = _parse_date(lent_on_text) if lent_on_text else clock.today()
    if lent_on > clock.today():
        raise RejectedError("貸出日に未来の日付は指定できません")

    if _open_loans("item_code = :c", {"c": item["code"]}):
        raise RejectedError("この物は貸出中です")
    mine = _open_loans("employee_no = :e", {"e": employee_no})
    if any(row["state"] == "overdue" for row in mine):
        raise RejectedError("返却の期限を過ぎた貸出があるため、貸し出せません")
    if len(mine) >= MAX_LOANS_PER_PERSON:
        raise RejectedError(f"1 人が同時に借りられるのは {MAX_LOANS_PER_PERSON} 件までです")

    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    get_db().execute(
        "INSERT INTO keys_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item["code"], employee_no, lent_on.isoformat(), due_on.isoformat()),
    )
    return item["code"]


def return_item(item_code):
    item = _require_item(item_code)
    loans = _open_loans("item_code = :c", {"c": item["code"]})
    if not loans:
        raise RejectedError("この物は貸出中ではありません")
    get_db().execute("UPDATE keys_loans SET returned_on = ? WHERE id = ?", (_today_text(), loans[0]["id"]))
    return item["code"]


def list_items(query=""):
    """物の一覧。貸出中なら借り手・貸出日・期限と、延滞かどうか（state）を付ける。"""
    like = f"%{query.strip()}%"
    rows = get_db().execute(
        f"""
        SELECT i.code, i.name, l.employee_no, l.lent_on, l.due_on, l.state, e.name AS employee_name
        FROM keys_items i
        LEFT JOIN (SELECT *, {LOAN_STATE_SQL} FROM keys_loans WHERE returned_on IS NULL) l ON l.item_code = i.code
        LEFT JOIN employees e ON e.employee_no = l.employee_no
        WHERE i.code LIKE :q OR i.name LIKE :q
        ORDER BY i.code
        """,
        {"today": _today_text(), "q": like},
    ).fetchall()
    return rows


def list_history():
    """返却済みの貸出（新しい順）。"""
    return get_db().execute(
        """
        SELECT l.*, i.name AS item_name, e.name AS employee_name
        FROM keys_loans l
        LEFT JOIN keys_items i ON i.code = l.item_code
        LEFT JOIN employees e ON e.employee_no = l.employee_no
        WHERE l.returned_on IS NOT NULL
        ORDER BY l.returned_on DESC, l.id DESC
        """
    ).fetchall()

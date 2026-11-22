"""来客用入館証の貸出の判定。受け付けないときは RuleError を投げる（画面側で 400 にする）。"""

import datetime

from app.core import audit, clock
from app.core.db import get_db

# 貸出の期間（日）と、1 人が同時に借りられる件数の上限
LOAN_DAYS = 1
MAX_PER_PERSON = 3


class RuleError(Exception):
    """入力や状態がきまりに合わない。メッセージは画面にそのまま出す。"""


def _clean(value):
    return (value or "").strip()


def _find_item(code):
    return get_db().execute("SELECT * FROM guest_badges_items WHERE code = ?", (code,)).fetchone()


def _open_loan(code):
    return get_db().execute(
        "SELECT * FROM guest_badges_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def create_item(code, name):
    code, name = _clean(code), _clean(name)
    if not code or not name:
        raise RuleError("番号と名前を入力してください")
    if _find_item(code):
        raise RuleError("この番号は既に登録されています")
    conn = get_db()
    conn.execute("INSERT INTO guest_badges_items (code, name) VALUES (?, ?)", (code, name))
    audit.record("guest_badges", "item_create", code)
    conn.commit()


def update_item(code, name):
    code, name = _clean(code), _clean(name)
    if _find_item(code) is None:
        raise RuleError("入館証が見つかりません")
    if not name:
        raise RuleError("名前を入力してください")
    conn = get_db()
    conn.execute("UPDATE guest_badges_items SET name = ? WHERE code = ?", (name, code))
    audit.record("guest_badges", "item_update", code)
    conn.commit()


def delete_item(code):
    code = _clean(code)
    if _find_item(code) is None:
        raise RuleError("入館証が見つかりません")
    if _open_loan(code):
        raise RuleError("貸出中の入館証は削除できません")
    conn = get_db()
    conn.execute("DELETE FROM guest_badges_items WHERE code = ?", (code,))
    audit.record("guest_badges", "item_delete", code)
    conn.commit()


def lend(item_code, employee_no, lent_on_text):
    """貸し出す。在籍の社員だけが対象で、件数の上限と期限切れの貸出の有無も見る。"""
    item_code, employee_no = _clean(item_code), _clean(employee_no)
    today = clock.today()
    conn = get_db()

    if _find_item(item_code) is None:
        raise RuleError("入館証が見つかりません")
    employee = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        raise RuleError("社員が見つかりません")
    if employee["status"] != "active":
        raise RuleError("退職した社員には貸し出せません")

    text = _clean(lent_on_text)
    if text:
        try:
            lent_on = datetime.date.fromisoformat(text)
        except ValueError:
            raise RuleError("貸出日は YYYY-MM-DD で入力してください")
        if len(text) != 10:
            raise RuleError("貸出日は YYYY-MM-DD で入力してください")
    else:
        lent_on = today
    if lent_on > today:
        raise RuleError("未来の日付は指定できません")

    if _open_loan(item_code):
        raise RuleError("この入館証は貸出中です")

    held = conn.execute(
        "SELECT COUNT(*) FROM guest_badges_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchone()[0]
    if held >= MAX_PER_PERSON:
        raise RuleError(f"同時に借りられるのは {MAX_PER_PERSON} 件までです")

    # 返却の期限を過ぎた貸出を持つ社員には貸さない
    expired = conn.execute(
        "SELECT COUNT(*) FROM guest_badges_loans WHERE employee_no = ? AND returned_on IS NULL AND due_on < ?",
        (employee_no, today.isoformat()),
    ).fetchone()[0]
    if expired:
        raise RuleError("返却の期限を過ぎた貸出があるため、新しく貸し出せません")

    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    conn.execute(
        "INSERT INTO guest_badges_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item_code, employee_no, lent_on.isoformat(), due_on.isoformat()),
    )
    audit.record("guest_badges", "lend", item_code)
    conn.commit()


def give_back(item_code):
    item_code = _clean(item_code)
    if _find_item(item_code) is None:
        raise RuleError("入館証が見つかりません")
    loan = _open_loan(item_code)
    if loan is None:
        raise RuleError("この入館証は貸出中ではありません")
    conn = get_db()
    conn.execute("UPDATE guest_badges_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
    audit.record("guest_badges", "return", item_code)
    conn.commit()


def list_items(query=""):
    """一覧用の行。借りている社員の名前と期限の判定（今日 > 期限）も含める。"""
    query = _clean(query)
    sql = (
        "SELECT i.code, i.name, l.employee_no AS borrower, e.name AS borrower_name, l.lent_on, l.due_on, "
        "CASE WHEN l.id IS NULL THEN 'free' WHEN l.due_on < ? THEN 'overdue' ELSE 'lent' END AS status "
        "FROM guest_badges_items i "
        "LEFT JOIN guest_badges_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
    )
    params = [clock.today().isoformat()]
    if query:
        sql += "WHERE i.code LIKE ? OR i.name LIKE ? "
        params += [f"%{query}%", f"%{query}%"]
    sql += "ORDER BY i.code"
    return get_db().execute(sql, params).fetchall()


def list_history():
    return get_db().execute(
        "SELECT l.item_code, i.name AS item_name, l.employee_no, e.name AS employee_name, l.lent_on, l.due_on, l.returned_on "
        "FROM guest_badges_loans l LEFT JOIN guest_badges_items i ON i.code = l.item_code "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()

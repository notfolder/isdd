"""モバイル機器の貸出の処理。画面（__init__.py）から呼ばれる。"""

import datetime
import sqlite3
from dataclasses import dataclass
from typing import Optional

from app.core import clock

LOAN_DAYS = 30  # 貸出の期間（日）
MAX_LOANS_PER_PERSON = 1  # 1 人が同時に借りられる件数


class RuleError(Exception):
    """きまりに合わない操作。メッセージは画面にそのまま出す。"""


@dataclass
class Item:
    code: str
    name: str


@dataclass
class Loan:
    item_code: str
    employee_no: str
    lent_on: datetime.date
    due_on: datetime.date


@dataclass
class ItemStatus:
    code: str
    name: str
    status: str  # free / lent / overdue
    borrower: Optional[str]
    lent_on: Optional[str]
    due_on: Optional[str]


def days_past_due(due_on: datetime.date, today: datetime.date) -> int:
    """返却の期限を過ぎた日数。期限当日までは 0。"""
    return max((today - due_on).days, 0)


def _loan_from_row(row) -> Loan:
    return Loan(
        item_code=row["item_code"],
        employee_no=row["employee_no"],
        lent_on=datetime.date.fromisoformat(row["lent_on"]),
        due_on=datetime.date.fromisoformat(row["due_on"]),
    )


def _open_loan_of_item(conn: sqlite3.Connection, code: str) -> Optional[Loan]:
    row = conn.execute("SELECT * FROM devices_loans WHERE item_code = ? AND returned_on IS NULL", (code,)).fetchone()
    return _loan_from_row(row) if row else None


def _open_loans_of_employee(conn: sqlite3.Connection, employee_no: str) -> list:
    rows = conn.execute("SELECT * FROM devices_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)).fetchall()
    return [_loan_from_row(r) for r in rows]


def _require_item(conn: sqlite3.Connection, code: str) -> Item:
    row = conn.execute("SELECT code, name FROM devices_items WHERE code = ?", (code,)).fetchone()
    if row is None:
        raise RuleError("その番号の機器は登録されていません")
    return Item(row["code"], row["name"])


def create_item(conn: sqlite3.Connection, code: str, name: str) -> Item:
    code, name = code.strip(), name.strip()
    if not code:
        raise RuleError("番号を入力してください")
    if not name:
        raise RuleError("名前を入力してください")
    if conn.execute("SELECT 1 FROM devices_items WHERE code = ?", (code,)).fetchone():
        raise RuleError("この番号は既に登録されています")
    conn.execute("INSERT INTO devices_items (code, name) VALUES (?, ?)", (code, name))
    return Item(code, name)


def update_item(conn: sqlite3.Connection, code: str, name: str) -> Item:
    code, name = code.strip(), name.strip()
    item = _require_item(conn, code)
    if not name:
        raise RuleError("名前を入力してください")
    conn.execute("UPDATE devices_items SET name = ? WHERE code = ?", (name, item.code))
    return Item(item.code, name)


def delete_item(conn: sqlite3.Connection, code: str) -> Item:
    item = _require_item(conn, code.strip())
    if _open_loan_of_item(conn, item.code):
        raise RuleError("貸出中の機器は削除できません")
    conn.execute("DELETE FROM devices_items WHERE code = ?", (item.code,))
    return item


def lend(conn: sqlite3.Connection, item_code: str, employee_no: str, lent_on_text: str) -> Loan:
    """貸し出す。きまりに合わなければ RuleError。"""
    today = clock.today()
    item = _require_item(conn, item_code.strip())
    employee_no = employee_no.strip()
    # 在籍している社員だけが対象（退職者・存在しない番号は行が返らない）
    employee = conn.execute("SELECT employee_no FROM employees WHERE employee_no = ? AND status = 'active'", (employee_no,)).fetchone()
    if employee is None:
        raise RuleError("在籍している社員ではありません")
    lent_on_text = lent_on_text.strip()
    if lent_on_text:
        try:
            lent_on = datetime.date.fromisoformat(lent_on_text)
        except ValueError:
            raise RuleError("貸出日は YYYY-MM-DD で入力してください")
        if lent_on > today:
            raise RuleError("貸出日に未来の日付は指定できません")
    else:
        lent_on = today
    if _open_loan_of_item(conn, item.code):
        raise RuleError("この機器は貸出中です")
    holding = _open_loans_of_employee(conn, employee_no)
    if any(days_past_due(loan.due_on, today) > 0 for loan in holding):
        raise RuleError("返却の期限を過ぎた機器があるため、新しく貸せません")
    if len(holding) >= MAX_LOANS_PER_PERSON:
        raise RuleError("1 人が同時に借りられるのは 1 件までです")
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    conn.execute(
        "INSERT INTO devices_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (item.code, employee_no, lent_on.isoformat(), due_on.isoformat()),
    )
    return Loan(item.code, employee_no, lent_on, due_on)


def return_item(conn: sqlite3.Connection, item_code: str) -> Item:
    """返却する。貸出の記録は returned_on を入れて履歴に残す。"""
    item = _require_item(conn, item_code.strip())
    if _open_loan_of_item(conn, item.code) is None:
        raise RuleError("この機器は貸出中ではありません")
    conn.execute(
        "UPDATE devices_loans SET returned_on = ? WHERE item_code = ? AND returned_on IS NULL",
        (clock.today().isoformat(), item.code),
    )
    return item


def list_status(conn: sqlite3.Connection, q: str = "") -> list:
    """機器の一覧（番号の昇順）。q があれば番号か名前の一部で絞り込む。"""
    today = clock.today()
    result = []
    for row in conn.execute("SELECT code, name FROM devices_items ORDER BY code").fetchall():
        if q and q not in row["code"] and q not in row["name"]:
            continue
        loan = _open_loan_of_item(conn, row["code"])
        if loan is None:
            result.append(ItemStatus(row["code"], row["name"], "free", None, None, None))
            continue
        state = "overdue" if days_past_due(loan.due_on, today) > 0 else "lent"
        result.append(ItemStatus(row["code"], row["name"], state, loan.employee_no, loan.lent_on.isoformat(), loan.due_on.isoformat()))
    return result


def list_history(conn: sqlite3.Connection) -> list:
    """返却済みの貸出（新しい順）。"""
    return conn.execute(
        "SELECT l.item_code, i.name AS item_name, l.employee_no, e.name AS employee_name, l.lent_on, l.due_on, l.returned_on "
        "FROM devices_loans l LEFT JOIN devices_items i ON i.code = l.item_code "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()

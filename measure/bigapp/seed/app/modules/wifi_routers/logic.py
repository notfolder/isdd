"""モバイル Wi-Fi の貸出の処理。画面（__init__.py）から呼ばれ、判定とデータの更新をここに集める。"""

import datetime
import sqlite3
from dataclasses import dataclass
from typing import Optional

from app.core import audit, clock
from app.core.db import get_db

# 貸出の期間（日）。返却の期限 = 貸出日 + LOAN_DAYS
LOAN_DAYS = 5
# 1 人が同時に借りられる件数の上限
MAX_LOANS_PER_EMPLOYEE = 1
# 貸出の対象にできない社員の状態（退職した社員）
EXCLUDED_STATUSES = {"retired"}


class RuleError(Exception):
    """きまりに合わず受け付けないとき。メッセージは画面にそのまま出す。"""


@dataclass
class Item:
    code: str
    name: str
    status: str  # free / lent / overdue
    borrower: Optional[str] = None
    lent_on: Optional[str] = None
    due_on: Optional[str] = None
    borrower_name: Optional[str] = None


@dataclass
class HistoryRow:
    item_code: str
    item_name: str
    employee_no: str
    employee_name: str
    lent_on: str
    due_on: str
    returned_on: str


def _iso(d: datetime.date) -> str:
    return d.isoformat()


def due_date(lent_on: datetime.date) -> datetime.date:
    """貸出日から返却の期限を求める。"""
    return lent_on + datetime.timedelta(days=LOAN_DAYS)


def _status(due_on: Optional[str]) -> str:
    """貸出中の物の状態。今日が期限より後なら overdue。"""
    if due_on is None:
        return "free"
    return "overdue" if clock.today() > datetime.date.fromisoformat(due_on) else "lent"


def _open_loan(conn: sqlite3.Connection, item_code: str):
    return conn.execute(
        "SELECT * FROM wifi_routers_loans WHERE item_code = ? AND returned_on IS NULL", (item_code,)
    ).fetchone()


def list_items(query: str = "") -> list:
    """物の一覧（番号の昇順）。query があれば番号か名前の一部で絞り込む。"""
    rows = get_db().execute(
        """
        SELECT i.code, i.name, l.employee_no, l.lent_on, l.due_on, e.name AS employee_name
        FROM wifi_routers_items i
        LEFT JOIN wifi_routers_loans l ON l.item_code = i.code AND l.returned_on IS NULL
        LEFT JOIN employees e ON e.employee_no = l.employee_no
        ORDER BY i.code
        """
    ).fetchall()
    q = query.strip().lower()
    items = []
    for r in rows:
        if q and q not in r["code"].lower() and q not in r["name"].lower():
            continue
        items.append(
            Item(r["code"], r["name"], _status(r["due_on"]), r["employee_no"], r["lent_on"], r["due_on"], r["employee_name"])
        )
    return items


def list_history() -> list:
    """返却済みの貸出の一覧（新しい順）。"""
    rows = get_db().execute(
        """
        SELECT l.*, e.name AS employee_name FROM wifi_routers_loans l
        LEFT JOIN employees e ON e.employee_no = l.employee_no
        WHERE l.returned_on IS NOT NULL
        ORDER BY l.lent_on DESC, l.id DESC
        """
    ).fetchall()
    return [
        HistoryRow(r["item_code"], r["item_name"], r["employee_no"], r["employee_name"] or "", r["lent_on"], r["due_on"], r["returned_on"])
        for r in rows
    ]


def has_overdue_loan(employee_no: str) -> bool:
    """その社員が、返却の期限を過ぎた（今日 > 期限）貸出を持っているか。"""
    rows = get_db().execute(
        "SELECT due_on FROM wifi_routers_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchall()
    return any(_status(r["due_on"]) == "overdue" for r in rows)


def _count_loans(employee_no: str) -> int:
    return get_db().execute(
        "SELECT COUNT(*) FROM wifi_routers_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchone()[0]


def _require_item(code: str):
    item = get_db().execute("SELECT * FROM wifi_routers_items WHERE code = ?", (code,)).fetchone()
    if item is None:
        raise RuleError("その番号の物は登録されていません")
    return item


def create_item(code: str, name: str) -> None:
    code, name = code.strip(), name.strip()
    if not code:
        raise RuleError("番号を入力してください")
    if not name:
        raise RuleError("名前を入力してください")
    conn = get_db()
    if conn.execute("SELECT 1 FROM wifi_routers_items WHERE code = ?", (code,)).fetchone():
        raise RuleError("この番号は既に登録されています")
    conn.execute("INSERT INTO wifi_routers_items (code, name) VALUES (?, ?)", (code, name))
    audit.record("wifi_routers", "item_create", code)
    conn.commit()


def update_item(code: str, name: str) -> None:
    code, name = code.strip(), name.strip()
    _require_item(code)
    if not name:
        raise RuleError("名前を入力してください")
    conn = get_db()
    conn.execute("UPDATE wifi_routers_items SET name = ? WHERE code = ?", (name, code))
    audit.record("wifi_routers", "item_update", code)
    conn.commit()


def delete_item(code: str) -> None:
    code = code.strip()
    _require_item(code)
    conn = get_db()
    if _open_loan(conn, code):
        raise RuleError("貸出中の物は削除できません")
    conn.execute("DELETE FROM wifi_routers_items WHERE code = ?", (code,))
    audit.record("wifi_routers", "item_delete", code)
    conn.commit()


def _parse_lent_on(text: str) -> datetime.date:
    """貸出日。省略なら今日。未来の日付は受け付けない。"""
    text = text.strip()
    if not text:
        return clock.today()
    try:
        d = datetime.date.fromisoformat(text)
    except ValueError:
        raise RuleError("貸出日は YYYY-MM-DD の形で入力してください")
    if d > clock.today():
        raise RuleError("貸出日に未来の日付は指定できません")
    return d


def lend(item_code: str, employee_no: str, lent_on_text: str) -> None:
    item_code, employee_no = item_code.strip(), employee_no.strip()
    conn = get_db()
    item = _require_item(item_code)
    if _open_loan(conn, item_code):
        raise RuleError("この物は貸出中です")
    emp = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if emp is None:
        raise RuleError("社員が見つかりません")
    if emp["status"] in EXCLUDED_STATUSES:
        raise RuleError("退職した社員には貸し出せません")
    if has_overdue_loan(employee_no):
        raise RuleError("返却の期限を過ぎた貸出があるため、貸し出せません")
    if _count_loans(employee_no) >= MAX_LOANS_PER_EMPLOYEE:
        raise RuleError("1 人が同時に借りられるのは 1 件までです")
    lent_on = _parse_lent_on(lent_on_text)
    conn.execute(
        "INSERT INTO wifi_routers_loans (item_code, item_name, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?, ?)",
        (item_code, item["name"], employee_no, _iso(lent_on), _iso(due_date(lent_on))),
    )
    audit.record("wifi_routers", "lend", f"{item_code}:{employee_no}")
    conn.commit()


def return_item(item_code: str) -> None:
    item_code = item_code.strip()
    conn = get_db()
    _require_item(item_code)
    loan = _open_loan(conn, item_code)
    if loan is None:
        raise RuleError("この物は貸出中ではありません")
    conn.execute("UPDATE wifi_routers_loans SET returned_on = ? WHERE id = ?", (_iso(clock.today()), loan["id"]))
    audit.record("wifi_routers", "return", item_code)
    conn.commit()

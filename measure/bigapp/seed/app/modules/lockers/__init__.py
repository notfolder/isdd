"""ロッカーの貸与。物の登録、貸出、返却、履歴、状態の JSON を扱う。"""

import datetime

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db

bp = Blueprint("lockers", __name__, url_prefix="/lockers", template_folder="templates")
TITLE = "ロッカーの貸与"

# 貸出の期間（日）
LOAN_DAYS = 90

SCHEMA = """
CREATE TABLE IF NOT EXISTS lockers_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lockers_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""


def days_past_due(due_on):
    """返却の期限（YYYY-MM-DD の文字列）を過ぎた日数。期限内なら 0 以下。"""
    return (clock.today() - datetime.date.fromisoformat(due_on)).days


def render_index(error=None, status=200):
    """一覧の画面を作る。絞り込み（q）があれば番号か名前の一部で絞る。"""
    q = request.args.get("q", "").strip()
    rows = _item_rows(q)
    return render_template("lockers/index.html", rows=rows, q=q, error=error), status


def _item_rows(q=""):
    """物の一覧。貸出中なら借りている社員と日付を付ける。code の昇順。"""
    sql = (
        "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, e.name AS borrower_name "
        "FROM lockers_items i "
        "LEFT JOIN lockers_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no"
    )
    args = ()
    if q:
        sql += " WHERE i.code LIKE ? OR i.name LIKE ?"
        args = (f"%{q}%", f"%{q}%")
    sql += " ORDER BY i.code"
    result = []
    for r in get_db().execute(sql, args).fetchall():
        row = dict(r)
        if row["borrower"] is None:
            row["status"] = "free"
        elif days_past_due(row["due_on"]) > 0:
            row["status"] = "overdue"
        else:
            row["status"] = "lent"
        result.append(row)
    return result


def _item_exists(code):
    return get_db().execute("SELECT 1 FROM lockers_items WHERE code = ?", (code,)).fetchone() is not None


def _current_loan(code):
    """物の貸出中の記録。貸出中でなければ None。"""
    return get_db().execute(
        "SELECT * FROM lockers_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def _reject(message):
    """受け付けないときの応答。データは変えない。"""
    return render_index(error=message, status=400)


@bp.route("/")
@login_required
def index():
    return render_index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if not code:
        return _reject("番号を入力してください")
    if not name:
        return _reject("名前を入力してください")
    if _item_exists(code):
        return _reject("この番号は既に登録されています")
    conn = get_db()
    conn.execute("INSERT INTO lockers_items (code, name) VALUES (?, ?)", (code, name))
    audit.record("lockers", "item_create", code)
    conn.commit()
    return redirect("/lockers/")


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if not _item_exists(code):
        return _reject("物が見つかりません")
    if not name:
        return _reject("名前を入力してください")
    conn = get_db()
    conn.execute("UPDATE lockers_items SET name = ? WHERE code = ?", (name, code))
    audit.record("lockers", "item_update", code)
    conn.commit()
    return redirect("/lockers/")


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    if not _item_exists(code):
        return _reject("物が見つかりません")
    if _current_loan(code) is not None:
        return _reject("貸出中の物は削除できません")
    conn = get_db()
    conn.execute("DELETE FROM lockers_items WHERE code = ?", (code,))
    audit.record("lockers", "item_delete", code)
    conn.commit()
    return redirect("/lockers/")


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code = request.form.get("item_code", "").strip()
    number = request.form.get("employee_no", "").strip()
    lent_text = request.form.get("lent_on", "").strip()
    conn = get_db()
    if not _item_exists(code):
        return _reject("物が見つかりません")
    employee = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
    if employee is None:
        return _reject("社員が見つかりません")
    if employee["status"] == "retired":
        return _reject("退職した社員には貸せません")
    if lent_text:
        try:
            lent_on = datetime.date.fromisoformat(lent_text)
        except ValueError:
            return _reject("貸出日は YYYY-MM-DD で入力してください")
    else:
        lent_on = clock.today()
    if lent_on > clock.today():
        return _reject("貸出日に未来の日付は指定できません")
    if _current_loan(code) is not None:
        return _reject("貸出中の物は貸せません")
    for loan in conn.execute(
        "SELECT due_on FROM lockers_loans WHERE employee_no = ? AND returned_on IS NULL", (number,)
    ).fetchall():
        if days_past_due(loan["due_on"]) > 0:
            return _reject("返却の期限を過ぎた貸出があるため貸せません")
        return _reject("1 人が同時に借りられるのは 1 件までです")
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    conn.execute(
        "INSERT INTO lockers_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, number, lent_on.isoformat(), due_on.isoformat()),
    )
    audit.record("lockers", "lend", code)
    conn.commit()
    return redirect("/lockers/")


@bp.route("/return", methods=["POST"])
@staff_required
def item_return():
    code = request.form.get("item_code", "").strip()
    if not _item_exists(code):
        return _reject("物が見つかりません")
    loan = _current_loan(code)
    if loan is None:
        return _reject("貸出中ではありません")
    conn = get_db()
    conn.execute("UPDATE lockers_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
    audit.record("lockers", "return", code)
    conn.commit()
    return redirect("/lockers/")


@bp.route("/history")
@login_required
def history():
    rows = get_db().execute(
        "SELECT l.*, e.name AS borrower_name FROM lockers_loans l "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.lent_on DESC, l.id DESC"
    ).fetchall()
    return render_template("lockers/history.html", rows=rows)


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {
            "code": r["code"],
            "name": r["name"],
            "status": r["status"],
            "borrower": r["borrower"],
            "lent_on": r["lent_on"],
            "due_on": r["due_on"],
        }
        for r in _item_rows()
    ]
    return jsonify({"items": items})

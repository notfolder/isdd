"""備品の貸出。物の登録、貸出、返却、履歴、状態の JSON を扱う（総務規程 第 3 条・第 6 条・第 7 条）。"""

import datetime

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db

bp = Blueprint("equipment", __name__, url_prefix="/equipment", template_folder="templates")
TITLE = "備品の貸出"

LOAN_DAYS = 14  # 貸出の期間（日）
MAX_LOANS_PER_PERSON = 2  # 1 人が同時に借りられる件数

SCHEMA = """
CREATE TABLE IF NOT EXISTS equipment_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS equipment_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""


def get_item(code):
    """物を 1 件返す。無ければ None。"""
    return get_db().execute("SELECT * FROM equipment_items WHERE code = ?", (code,)).fetchone()


def get_open_loan(code):
    """物の貸出中の記録を返す。貸出中でなければ None。"""
    return get_db().execute(
        "SELECT * FROM equipment_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def count_open_loans(employee_no):
    """社員が今借りている件数。"""
    return get_db().execute(
        "SELECT COUNT(*) FROM equipment_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchone()[0]


def has_overdue_loan(employee_no):
    """返却の期限を過ぎた貸出（今日 > 期限）を、この機能で持っている社員なら True。"""
    today = clock.today().isoformat()
    row = get_db().execute(
        "SELECT 1 FROM equipment_loans WHERE employee_no = ? AND returned_on IS NULL AND due_on < ?",
        (employee_no, today),
    ).fetchone()
    return row is not None


def is_active_employee(employee_no):
    """在籍している社員なら True。退職者と存在しない番号は False。"""
    row = get_db().execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    return row is not None and row["status"] == "active"


def loan_status(loan):
    """貸出の記録から状態を返す。free / lent / overdue。"""
    if loan is None:
        return "free"
    return "overdue" if clock.today().isoformat() > loan["due_on"] else "lent"


def list_rows(query=""):
    """一覧に出す行（物 + 貸出中の情報）。番号の昇順。"""
    sql = (
        "SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, e.name AS borrower_name "
        "FROM equipment_items i "
        "LEFT JOIN equipment_loans l ON l.item_code = i.code AND l.returned_on IS NULL "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no"
    )
    params = []
    if query:
        sql += " WHERE i.code LIKE ? OR i.name LIKE ?"
        params = [f"%{query}%", f"%{query}%"]
    sql += " ORDER BY i.code"
    rows = []
    for r in get_db().execute(sql, params).fetchall():
        d = dict(r)
        d["status"] = "free" if r["borrower"] is None else loan_status({"due_on": r["due_on"]})
        rows.append(d)
    return rows


def render_index(error=None, status=200):
    """一覧の画面を返す。error があれば理由を出す。"""
    q = request.values.get("q", "").strip()
    return render_template("equipment/index.html", rows=list_rows(q), q=q, error=error), status


def fail(message):
    """受け付けないときの応答（HTTP 400。データは変えない）。"""
    return render_index(error=message, status=400)


def done():
    return redirect("/equipment/")


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
        return fail("番号を入力してください")
    if not name:
        return fail("名前を入力してください")
    if get_item(code):
        return fail("この番号は既に登録されています")
    conn = get_db()
    conn.execute("INSERT INTO equipment_items (code, name) VALUES (?, ?)", (code, name))
    audit.record("equipment", "item_create", code)
    conn.commit()
    return done()


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if get_item(code) is None:
        return fail("備品が見つかりません")
    if not name:
        return fail("名前を入力してください")
    conn = get_db()
    conn.execute("UPDATE equipment_items SET name = ? WHERE code = ?", (name, code))
    audit.record("equipment", "item_update", code)
    conn.commit()
    return done()


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    if get_item(code) is None:
        return fail("備品が見つかりません")
    if get_open_loan(code):
        return fail("貸出中の備品は削除できません")
    conn = get_db()
    conn.execute("DELETE FROM equipment_items WHERE code = ?", (code,))
    audit.record("equipment", "item_delete", code)
    conn.commit()
    return done()


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code = request.form.get("item_code", "").strip()
    employee_no = request.form.get("employee_no", "").strip()
    lent_text = request.form.get("lent_on", "").strip()
    item = get_item(code)
    if item is None:
        return fail("備品が見つかりません")
    if get_open_loan(code):
        return fail("この備品は貸出中です")
    if not is_active_employee(employee_no):
        return fail("在籍している社員を指定してください")
    if lent_text:
        try:
            lent_on = datetime.date.fromisoformat(lent_text)
        except ValueError:
            return fail("貸出日は YYYY-MM-DD で入力してください")
    else:
        lent_on = clock.today()
    if lent_on > clock.today():
        return fail("未来の日付は指定できません")
    if has_overdue_loan(employee_no):
        return fail("返却の期限を過ぎた貸出があるため、貸し出せません")
    if count_open_loans(employee_no) >= MAX_LOANS_PER_PERSON:
        return fail(f"1 人が同時に借りられるのは {MAX_LOANS_PER_PERSON} 件までです")
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    conn = get_db()
    conn.execute(
        "INSERT INTO equipment_loans (item_code, item_name, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?, ?)",
        (code, item["name"], employee_no, lent_on.isoformat(), due_on.isoformat()),
    )
    audit.record("equipment", "lend", code)
    conn.commit()
    return done()


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    loan = get_open_loan(code)
    if loan is None:
        return fail("貸出中の備品ではありません")
    conn = get_db()
    conn.execute("UPDATE equipment_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
    audit.record("equipment", "return", code)
    conn.commit()
    return done()


@bp.route("/history")
@login_required
def history():
    rows = get_db().execute(
        "SELECT l.*, e.name AS borrower_name FROM equipment_loans l "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()
    return render_template("equipment/history.html", rows=rows)


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
        for r in list_rows()
    ]
    return jsonify({"items": items})

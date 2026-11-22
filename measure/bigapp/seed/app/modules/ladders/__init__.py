"""脚立の貸出。物の台帳と、貸出・返却の記録を扱う。"""

import datetime

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db

bp = Blueprint("ladders", __name__, url_prefix="/ladders", template_folder="templates")
TITLE = "脚立の貸出"

# 貸出の期間（日）。返却の期限 = 貸出日 + LOAN_DAYS
LOAN_DAYS = 2
# 1 人が同時に借りられる件数の上限
MAX_LOANS = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS ladders_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ladders_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""


def get_item(code):
    """番号から物を 1 件取る。無ければ None。"""
    return get_db().execute("SELECT * FROM ladders_items WHERE code = ?", (code,)).fetchone()


def get_active_loan(code):
    """物の貸出中の記録（未返却）。貸出中でなければ None。"""
    return get_db().execute("SELECT * FROM ladders_loans WHERE item_code = ? AND returned_on IS NULL", (code,)).fetchone()


def find_employee(employee_no):
    """社員を取る。退職していない社員だけを対象にし、退職者と存在しない番号は None。"""
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ? AND status != 'retired'", (employee_no,)).fetchone()


def can_borrow(employee_no):
    """社員に新しく貸せるかを調べる。貸せなければ理由の文字列、貸せるなら None を返す。"""
    loans = get_db().execute("SELECT due_on FROM ladders_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)).fetchall()
    today = clock.today()
    # 返却の期限を過ぎた貸出を持つ社員には貸さない（今日 > 期限）
    if any(datetime.date.fromisoformat(r["due_on"]) < today for r in loans):
        return "返却の期限を過ぎた貸出があるため、貸し出せません"
    if len(loans) >= MAX_LOANS:
        return f"同時に借りられるのは {MAX_LOANS} 件までです"
    return None


def item_status(loan):
    """貸出の記録から状態を決める。free・lent・overdue のいずれか。"""
    if loan is None:
        return "free"
    if datetime.date.fromisoformat(loan["due_on"]) < clock.today():
        return "overdue"
    return "lent"


def list_items(q=""):
    """一覧用の行。物ごとに状態と借りている社員を付ける。番号の昇順。"""
    rows = get_db().execute(
        """SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on, e.name AS borrower_name
           FROM ladders_items i
           LEFT JOIN ladders_loans l ON l.item_code = i.code AND l.returned_on IS NULL
           LEFT JOIN employees e ON e.employee_no = l.employee_no
           ORDER BY i.code"""
    ).fetchall()
    result = []
    for r in rows:
        if q and q not in r["code"] and q not in r["name"]:
            continue
        item = dict(r)
        item["status"] = item_status(r if r["due_on"] else None)
        result.append(item)
    return result


def render_index(error=None, status=200):
    """一覧の画面を返す。error があれば理由を出す。"""
    q = request.values.get("q", "").strip() if request.method == "GET" else ""
    html = render_template("ladders/index.html", items=list_items(q), q=q, error=error, today=clock.today().isoformat())
    return html, status


def done(action, target):
    """操作の記録を残して確定し、一覧へ戻す。"""
    audit.record("ladders", action, target)
    get_db().commit()
    return redirect("/ladders/")


@bp.route("/")
@login_required
def index():
    return render_index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not code:
        return render_index("番号を入力してください", 400)
    if not name:
        return render_index("名前を入力してください", 400)
    if get_item(code):
        return render_index("この番号は既に登録されています", 400)
    get_db().execute("INSERT INTO ladders_items (code, name) VALUES (?, ?)", (code, name))
    return done("item_create", code)


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if get_item(code) is None:
        return render_index("物が見つかりません", 400)
    if not name:
        return render_index("名前を入力してください", 400)
    get_db().execute("UPDATE ladders_items SET name = ? WHERE code = ?", (name, code))
    return done("item_update", code)


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    if get_item(code) is None:
        return render_index("物が見つかりません", 400)
    if get_active_loan(code):
        return render_index("貸出中の物は削除できません", 400)
    get_db().execute("DELETE FROM ladders_items WHERE code = ?", (code,))
    return done("item_delete", code)


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code = request.form.get("item_code", "").strip()
    number = request.form.get("employee_no", "").strip()
    text = request.form.get("lent_on", "").strip()
    today = clock.today()
    if text:
        try:
            lent_on = datetime.date.fromisoformat(text)
        except ValueError:
            return render_index("貸出日は YYYY-MM-DD で入力してください", 400)
        if lent_on > today:
            return render_index("貸出日に未来の日付は指定できません", 400)
    else:
        lent_on = today
    if get_item(code) is None:
        return render_index("物が見つかりません", 400)
    if find_employee(number) is None:
        return render_index("在籍している社員が見つかりません", 400)
    if get_active_loan(code):
        return render_index("この物は貸出中です", 400)
    reason = can_borrow(number)
    if reason:
        return render_index(reason, 400)
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    get_db().execute(
        "INSERT INTO ladders_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, number, lent_on.isoformat(), due_on.isoformat()),
    )
    return done("lend", code)


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    loan = get_active_loan(code) if get_item(code) else None
    if loan is None:
        return render_index("貸出中の物ではありません", 400)
    get_db().execute("UPDATE ladders_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
    return done("return", code)


@bp.route("/history")
@login_required
def history():
    rows = get_db().execute(
        """SELECT l.*, e.name AS borrower_name FROM ladders_loans l
           LEFT JOIN employees e ON e.employee_no = l.employee_no
           WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"""
    ).fetchall()
    return render_template("ladders/history.html", rows=rows)


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {"code": i["code"], "name": i["name"], "status": i["status"], "borrower": i["borrower"], "lent_on": i["lent_on"], "due_on": i["due_on"]}
        for i in list_items()
    ]
    return jsonify({"items": items})

"""プロジェクターの貸出。物の登録、貸出、返却、履歴、状態の JSON を扱う。"""

import datetime

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db

bp = Blueprint("projectors", __name__, url_prefix="/projectors", template_folder="templates")
TITLE = "プロジェクターの貸出"

# 貸出の期間（日）と、1 人が同時に借りられる件数の上限
LOAN_DAYS = 2
MAX_LOANS_PER_PERSON = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS projectors_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projectors_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""


def find_item(code):
    """番号で物を探す。無ければ None。"""
    return get_db().execute("SELECT * FROM projectors_items WHERE code = ?", (code,)).fetchone()


def find_open_loan(code):
    """その物の貸出中の記録。貸出中でなければ None。"""
    return get_db().execute(
        "SELECT * FROM projectors_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def item_status(loan):
    """貸出の記録から状態を決める。free / lent / overdue。今日 > 期限 のとき overdue。"""
    if loan is None:
        return "free"
    if clock.today() > datetime.date.fromisoformat(loan["due_on"]):
        return "overdue"
    return "lent"


def can_borrow(employee_no):
    """社員に新しく貸せるかを調べる。貸せないときは理由の文字列、貸せるときは None を返す。"""
    loans = get_db().execute(
        "SELECT due_on FROM projectors_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchall()
    today = clock.today()
    # 返却の期限を過ぎた貸出を持つ社員には貸さない（総務規程 第 3 条）
    if any(today > datetime.date.fromisoformat(r["due_on"]) for r in loans):
        return "返却の期限を過ぎた貸出があるため、貸せません"
    if len(loans) >= MAX_LOANS_PER_PERSON:
        return "同時に借りられる件数の上限（%d 件）に達しています" % MAX_LOANS_PER_PERSON
    return None


def list_items(q=""):
    """一覧の行。番号か名前の一部で絞り込める。"""
    rows = get_db().execute("SELECT * FROM projectors_items ORDER BY code").fetchall()
    q = q.strip()
    result = []
    for r in rows:
        if q and q not in r["code"] and q not in r["name"]:
            continue
        loan = find_open_loan(r["code"])
        borrower = None
        if loan is not None:
            emp = get_db().execute("SELECT name FROM employees WHERE employee_no = ?", (loan["employee_no"],)).fetchone()
            borrower = {"no": loan["employee_no"], "name": emp["name"] if emp else ""}
        result.append({"code": r["code"], "name": r["name"], "status": item_status(loan), "borrower": borrower, "loan": loan})
    return result


def render_index(error=None, code=400):
    """一覧の画面を出す。error があれば理由を表示する。"""
    q = request.args.get("q", "")
    return render_template("projectors/index.html", rows=list_items(q), q=q, error=error, title=TITLE), code


def reject(message):
    """受け付けないときの返答。HTTP 400 で理由を出し、データは変えない。"""
    return render_index(message, 400)


def done(action, target):
    """操作を記録して確定し、一覧へ戻す。"""
    audit.record("projectors", action, target)
    get_db().commit()
    return redirect("/projectors/")


@bp.route("/")
@login_required
def index():
    return render_index(None, 200)


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if not code:
        return reject("番号を入力してください")
    if not name:
        return reject("名前を入力してください")
    if find_item(code):
        return reject("この番号は既に登録されています")
    get_db().execute("INSERT INTO projectors_items (code, name) VALUES (?, ?)", (code, name))
    return done("item_create", code)


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if find_item(code) is None:
        return reject("物が見つかりません")
    if not name:
        return reject("名前を入力してください")
    get_db().execute("UPDATE projectors_items SET name = ? WHERE code = ?", (name, code))
    return done("item_update", code)


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    if find_item(code) is None:
        return reject("物が見つかりません")
    if find_open_loan(code):
        return reject("貸出中の物は削除できません")
    get_db().execute("DELETE FROM projectors_items WHERE code = ?", (code,))
    return done("item_delete", code)


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code = request.form.get("item_code", "").strip()
    number = request.form.get("employee_no", "").strip()
    text = request.form.get("lent_on", "").strip()
    if find_item(code) is None:
        return reject("物が見つかりません")
    if find_open_loan(code):
        return reject("貸出中の物は貸せません")
    emp = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
    if emp is None:
        return reject("社員が見つかりません")
    active = emp["status"] == "active"
    if not active:
        return reject("退職した社員には貸せません")
    today = clock.today()
    if text:
        try:
            lent_on = datetime.date.fromisoformat(text)
        except ValueError:
            return reject("貸出日は YYYY-MM-DD の形で入力してください")
        if lent_on > today:
            return reject("貸出日に未来の日付は指定できません")
    else:
        lent_on = today
    reason = can_borrow(number)
    if reason:
        return reject(reason)
    due_on = lent_on + datetime.timedelta(days=LOAN_DAYS)
    get_db().execute(
        "INSERT INTO projectors_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, number, lent_on.isoformat(), due_on.isoformat()),
    )
    return done("lend", "%s:%s" % (code, number))


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    loan = find_open_loan(code)
    if loan is None:
        return reject("貸出中ではありません")
    get_db().execute("UPDATE projectors_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"]))
    return done("return", code)


@bp.route("/history")
@login_required
def history():
    rows = get_db().execute(
        "SELECT l.*, i.name AS item_name, e.name AS employee_name FROM projectors_loans l "
        "LEFT JOIN projectors_items i ON i.code = l.item_code "
        "LEFT JOIN employees e ON e.employee_no = l.employee_no "
        "WHERE l.returned_on IS NOT NULL ORDER BY l.returned_on DESC, l.id DESC"
    ).fetchall()
    return render_template("projectors/history.html", rows=rows, title=TITLE)


@bp.route("/status.json")
@login_required
def status_json():
    items = []
    for r in list_items():
        loan = r["loan"]
        items.append(
            {
                "code": r["code"],
                "name": r["name"],
                "status": r["status"],
                "borrower": loan["employee_no"] if loan else None,
                "lent_on": loan["lent_on"] if loan else None,
                "due_on": loan["due_on"] if loan else None,
            }
        )
    return jsonify({"items": items})

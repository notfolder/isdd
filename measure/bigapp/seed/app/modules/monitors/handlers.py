"""画面と URL。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.monitors import bp, queries, rules


def _rows(q=""):
    """一覧の表示用の行に状態を足す。"""
    today = clock.today()
    rows = []
    for r in queries.list_items(q):
        loan = {"due_on": r["due_on"]} if r["borrower"] else None
        rows.append({**dict(r), "status": rules.status_of(loan, today)})
    return rows


def _fail(message, q=""):
    """受け付けない。400 で理由を出し、データは変えない。"""
    get_db().rollback()
    return render_template("monitors/index.html", rows=_rows(q), q=q, error=message), 400


def _done():
    get_db().commit()
    return redirect(url_for("monitors.index"))


@bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    return render_template("monitors/index.html", rows=_rows(q), q=q, error=None)


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not code:
        return _fail("番号を入力してください")
    if not name:
        return _fail("名前を入力してください")
    if queries.get_item(code):
        return _fail("この番号は既に登録されています")
    queries.insert_item(code, name)
    audit.record("monitors", "item_create", code)
    return _done()


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not queries.get_item(code):
        return _fail("物が見つかりません")
    if not name:
        return _fail("名前を入力してください")
    queries.update_item(code, name)
    audit.record("monitors", "item_update", code)
    return _done()


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    if not queries.get_item(code):
        return _fail("物が見つかりません")
    if queries.get_open_loan(code):
        return _fail("貸出中の物は削除できません")
    queries.delete_item(code)
    audit.record("monitors", "item_delete", code)
    return _done()


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code = request.form.get("item_code", "").strip()
    number = request.form.get("employee_no", "").strip()
    today = clock.today()
    lent_on, error = rules.parse_lent_on(request.form.get("lent_on"), today)
    if error:
        return _fail(error)
    item = queries.get_item(code)
    if item and queries.get_open_loan(code):
        return _fail("貸出中の物は貸せません")
    employee = queries.get_active_employee(number)
    error = rules.check_lend(item, employee, queries.get_open_loans_of(number) if employee else [], today)
    if error:
        return _fail(error)
    queries.insert_loan(code, number, lent_on.isoformat(), rules.due_date(lent_on).isoformat())
    audit.record("monitors", "lend", f"{code}:{number}")
    return _done()


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    loan = queries.get_open_loan(code)
    if loan is None:
        return _fail("貸出中の物ではありません")
    queries.close_loan(loan["id"], clock.today().isoformat())
    audit.record("monitors", "return", code)
    return _done()


@bp.route("/history")
@login_required
def history():
    return render_template("monitors/history.html", rows=queries.list_history())


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
        for r in _rows()
    ]
    return jsonify({"items": items})

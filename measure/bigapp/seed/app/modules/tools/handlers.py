"""画面。入力を受け取り、rules.py で判定し、queries.py で読み書きする。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.tools import bp, queries, rules


def _page(error=None, status=200):
    """一覧の画面。error があれば 400 などで理由を出す。"""
    q = request.values.get("q", "").strip()
    today = clock.today()
    rows = [
        {
            "code": r["code"], "name": r["name"], "borrower": r["borrower"], "lent_on": r["lent_on"], "due_on": r["due_on"],
            "status": rules.item_status(r if r["borrower"] else None, today),
        }
        for r in queries.list_items(q)
    ]
    return render_template("tools/index.html", rows=rows, q=q, error=error, today=today.isoformat()), status


def _done():
    get_db().commit()
    return redirect(url_for("tools.index"))


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not code or not name:
        return _page("番号と名前を入力してください", 400)
    if queries.get_item(code):
        return _page("この番号は既に登録されています", 400)
    queries.insert_item(code, name)
    audit.record("tools", "item_create", code)
    return _done()


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not queries.get_item(code):
        return _page("物が見つかりません", 400)
    if not name:
        return _page("名前を入力してください", 400)
    queries.update_item(code, name)
    audit.record("tools", "item_update", code)
    return _done()


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    if not queries.get_item(code):
        return _page("物が見つかりません", 400)
    if queries.get_open_loan(code):
        return _page("貸出中の物は削除できません", 400)
    queries.delete_item(code)
    audit.record("tools", "item_delete", code)
    return _done()


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code = request.form.get("item_code", "").strip()
    employee_no = request.form.get("employee_no", "").strip()
    text = request.form.get("lent_on", "").strip()
    today = clock.today()
    if not queries.get_item(code):
        return _page("物が見つかりません", 400)
    lent_on = rules.parse_date(text) if text else today
    employee = queries.get_employee(employee_no)
    error = rules.check_lend(employee, queries.get_open_loan(code), queries.list_open_loans_of(employee_no), lent_on, today)
    if error:
        return _page(error, 400)
    queries.insert_loan(code, employee_no, lent_on.isoformat(), rules.due_date(lent_on).isoformat())
    audit.record("tools", "lend", f"{code}:{employee_no}")
    return _done()


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    loan = queries.get_open_loan(code)
    if loan is None:
        return _page("貸出中ではありません", 400)
    queries.close_loan(loan["id"], clock.today().isoformat())
    audit.record("tools", "return", code)
    return _done()


@bp.route("/history")
@login_required
def history():
    return render_template("tools/history.html", rows=queries.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    today = clock.today()
    items = [
        {
            "code": r["code"], "name": r["name"], "status": rules.item_status(r if r["borrower"] else None, today),
            "borrower": r["borrower"], "lent_on": r["lent_on"], "due_on": r["due_on"],
        }
        for r in queries.list_items()
    ]
    return jsonify({"items": items})

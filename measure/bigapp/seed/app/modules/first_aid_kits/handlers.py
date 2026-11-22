"""救急箱の貸出の画面。判定は rules.py、SQL は queries.py に任せる。"""

import sqlite3

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.modules.first_aid_kits import TITLE, bp, queries, rules


def _rows(q=""):
    """一覧の 1 行ごとの表示用の値を作る。"""
    today = clock.today()
    loans = queries.open_loans_by_item()
    rows = []
    for item in queries.list_items(q):
        loan = loans.get(item["code"])
        rows.append(
            {
                "code": item["code"],
                "name": item["name"],
                "status": rules.loan_status(loan, today),
                "borrower": loan["employee_no"] if loan else None,
                "lent_on": loan["lent_on"] if loan else None,
                "due_on": loan["due_on"] if loan else None,
            }
        )
    return rows


def _show_index(error=None, status=200):
    q = request.args.get("q", "").strip()
    return render_template("first_aid_kits/index.html", title=TITLE, rows=_rows(q), q=q, error=error), status


def _done():
    queries.commit()
    return redirect(url_for("first_aid_kits.index"))


@bp.route("/")
@login_required
def index():
    return _show_index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    error = rules.check_item_fields(code, name)
    if error is None and queries.find_item(code):
        error = "この番号は既に登録されています"
    if error:
        return _show_index(error, 400)
    try:
        queries.insert_item(code, name)
    except sqlite3.IntegrityError:
        return _show_index("この番号は既に登録されています", 400)
    audit.record("first_aid_kits", "item_create", code)
    return _done()


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    error = rules.check_item_fields(code, name)
    if error is None and queries.find_item(code) is None:
        error = "救急箱が見つかりません"
    if error:
        return _show_index(error, 400)
    queries.update_item(code, name)
    audit.record("first_aid_kits", "item_update", code)
    return _done()


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    error = None
    if queries.find_item(code) is None:
        error = "救急箱が見つかりません"
    elif queries.open_loan_of_item(code) is not None:
        error = "貸出中の救急箱は削除できません"
    if error:
        return _show_index(error, 400)
    queries.delete_item(code)
    audit.record("first_aid_kits", "item_delete", code)
    return _done()


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    today = clock.today()
    code = request.form.get("item_code", "").strip()
    employee_no = request.form.get("employee_no", "").strip()
    lent_on, error = rules.parse_lent_on(request.form.get("lent_on"), today)
    if error is None:
        employee = queries.find_active_employee(employee_no)
        error = rules.check_lend(
            queries.find_item(code),
            employee,
            queries.open_loan_of_item(code),
            queries.open_loans_of_employee(employee_no) if employee else [],
            today,
        )
    if error:
        return _show_index(error, 400)
    queries.insert_loan(code, employee_no, lent_on.isoformat(), rules.due_date(lent_on).isoformat())
    audit.record("first_aid_kits", "lend", code)
    return _done()


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    loan = queries.open_loan_of_item(code)
    if loan is None:
        return _show_index("貸出中ではありません", 400)
    queries.close_loan(loan["id"], clock.today().isoformat())
    audit.record("first_aid_kits", "return", code)
    return _done()


@bp.route("/history")
@login_required
def history():
    return render_template("first_aid_kits/history.html", title=TITLE, rows=queries.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": _rows()})

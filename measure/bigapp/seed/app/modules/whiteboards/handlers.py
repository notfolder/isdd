"""ホワイトボードの貸出の画面。データを変える操作は総務の担当者だけ。"""

import sqlite3

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.whiteboards import bp, queries, rules


def _today() -> str:
    return clock.today().isoformat()


def _render_index(error=None, status=200):
    q = request.args.get("q", "").strip()
    items = queries.list_items(_today(), q)
    return render_template("whiteboards/index.html", items=items, q=q, error=error), status


def _fail(message):
    """受け付けないとき。400 で理由を出し、データは変えない。"""
    get_db().rollback()
    return _render_index(message, 400)


def _done():
    get_db().commit()
    return redirect(url_for("whiteboards.index"))


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if not code or not name:
        return _fail("番号と名前を入力してください")
    try:
        queries.insert_item(code, name)
    except sqlite3.IntegrityError:
        return _fail("この番号は既に登録されています")
    audit.record("whiteboards", "item_create", code)
    return _done()


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if not name:
        return _fail("名前を入力してください")
    if queries.get_item(code, _today()) is None:
        return _fail("物が見つかりません")
    queries.update_item(code, name)
    audit.record("whiteboards", "item_update", code)
    return _done()


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    item = queries.get_item(code, _today())
    if item is None:
        return _fail("物が見つかりません")
    if item["state"] != "free":
        return _fail("貸出中の物は削除できません")
    queries.delete_item(code)
    audit.record("whiteboards", "item_delete", code)
    return _done()


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    today = clock.today()
    code = request.form.get("item_code", "").strip()
    number = request.form.get("employee_no", "").strip()
    lent_on, date_error = rules.parse_lent_on(request.form.get("lent_on", ""), today)
    item = queries.get_item(code, today.isoformat())
    employee = queries.get_active_employee(number)
    active, overdue = queries.count_loans(number, today.isoformat())
    error = rules.check_lend(item, employee, date_error, active, overdue)
    if error:
        return _fail(error)
    queries.insert_loan(code, number, lent_on.isoformat(), rules.due_date(lent_on).isoformat())
    audit.record("whiteboards", "lend", f"{code}:{number}")
    return _done()


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    item = queries.get_item(code, _today())
    if item is None:
        return _fail("物が見つかりません")
    if item["state"] == "free":
        return _fail("この物は貸し出されていません")
    queries.close_loan(code, _today())
    audit.record("whiteboards", "return", code)
    return _done()


@bp.route("/history")
@login_required
def history():
    return render_template("whiteboards/history.html", rows=queries.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {"code": r["code"], "name": r["name"], "status": r["state"], "borrower": r["borrower"],
         "lent_on": r["lent_on"], "due_on": r["due_on"]}
        for r in queries.list_items(_today())
    ]
    return jsonify({"items": items})

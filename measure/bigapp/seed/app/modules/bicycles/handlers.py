"""社用自転車の画面。データを変える操作は総務の担当者だけができる。"""

import sqlite3

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.bicycles import bp, queries, rules


def _page(error=None, status=200):
    """一覧の画面を描く。error があれば理由を出す。"""
    q = rules.clean(request.args.get("q"))
    rows = queries.list_items(q)
    today = clock.today().isoformat()
    return render_template("bicycles/index.html", rows=rows, q=q, today=today, error=error), status


def _reject(error):
    """受け付けない。400 で理由を出し、データは変えない。"""
    get_db().rollback()
    return _page(error, 400)


def _done():
    return redirect(url_for("bicycles.index"))


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code, name = rules.clean(request.form.get("code")), rules.clean(request.form.get("name"))
    error = rules.check_item_fields(code, name)
    if error:
        return _reject(error)
    if queries.get_item(code):
        return _reject("この番号は既に登録されています")
    try:
        queries.insert_item(code, name)
    except sqlite3.IntegrityError:
        return _reject("この番号は既に登録されています")
    audit.record("bicycles", "item_create", code)
    get_db().commit()
    return _done()


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code, name = rules.clean(request.form.get("code")), rules.clean(request.form.get("name"))
    error = rules.check_item_fields(code, name)
    if error:
        return _reject(error)
    if not queries.get_item(code):
        return _reject("その番号の自転車はありません")
    queries.update_item(code, name)
    audit.record("bicycles", "item_update", code)
    get_db().commit()
    return _done()


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = rules.clean(request.form.get("code"))
    if not queries.get_item(code):
        return _reject("その番号の自転車はありません")
    if queries.open_loan_of_item(code):
        return _reject("貸出中の自転車は削除できません")
    queries.delete_item(code)
    audit.record("bicycles", "item_delete", code)
    get_db().commit()
    return _done()


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code = rules.clean(request.form.get("item_code"))
    employee_no = rules.clean(request.form.get("employee_no"))
    lent_text = rules.clean(request.form.get("lent_on"))
    today = clock.today()

    if not queries.get_item(code):
        return _reject("その番号の自転車はありません")
    employee = queries.get_employee(employee_no)
    if employee is None:
        return _reject("社員が見つかりません")
    if rules.is_retired(employee):
        return _reject("退職した社員には貸し出せません")
    if lent_text:
        lent_on = rules.parse_date(lent_text)
        if lent_on is None:
            return _reject("貸出日は YYYY-MM-DD で入力してください")
        if lent_on > today:
            return _reject("貸出日に未来の日付は指定できません")
    else:
        lent_on = today
    if queries.open_loan_of_item(code):
        return _reject("この自転車は貸出中です")
    held = queries.open_loan_of_employee(employee_no)
    if held:
        # 期限を過ぎた貸出を持つ社員には新しく貸さない
        if today.isoformat() > held["due_on"]:
            return _reject("返却の期限を過ぎた貸出があるため、貸し出せません")
        return _reject("この社員は既に借りています（同時に借りられるのは 1 件までです）")

    queries.insert_loan(code, employee_no, lent_on.isoformat(), rules.due_date(lent_on).isoformat())
    audit.record("bicycles", "lend", code)
    get_db().commit()
    return _done()


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = rules.clean(request.form.get("item_code"))
    if not queries.get_item(code):
        return _reject("その番号の自転車はありません")
    loan = queries.open_loan_of_item(code)
    if loan is None:
        return _reject("この自転車は貸出中ではありません")
    queries.close_loan(loan["id"], clock.today().isoformat())
    audit.record("bicycles", "return", code)
    get_db().commit()
    return _done()


@bp.route("/history")
@login_required
def history():
    return render_template("bicycles/history.html", rows=queries.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    today = clock.today().isoformat()
    items = []
    for r in queries.list_items(""):
        if r["borrower"] is None:
            status = "free"
        elif today > r["due_on"]:
            status = "overdue"
        else:
            status = "lent"
        items.append({"code": r["code"], "name": r["name"], "status": status,
                      "borrower": r["borrower"], "lent_on": r["lent_on"], "due_on": r["due_on"]})
    return jsonify({"items": items})

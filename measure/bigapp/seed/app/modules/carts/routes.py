"""台車の貸出の画面。"""

import datetime

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import clock
from app.core.auth import login_required, staff_required
from app.modules.carts import repo, service

bp = Blueprint("carts", __name__, url_prefix="/carts", template_folder="templates")


def _page(error=None, status=200):
    q = request.values.get("q", "").strip()
    return render_template("carts/index.html", items=service.status_list(q), q=q, error=error), status


def _run(action, *args):
    """処理を実行し、受け付けなければ 400 で理由を出す。成功したら一覧へ戻す。"""
    try:
        action(*args)
    except service.Rejected as e:
        return _page(str(e), 400)
    return redirect("/carts/")


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_new():
    return _run(service.create_item, request.form.get("code", ""), request.form.get("name", ""))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_edit():
    return _run(service.update_item, request.form.get("code", ""), request.form.get("name", ""))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _run(service.delete_item, request.form.get("code", ""))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    """貸し出す。返却の期限を過ぎた貸出を持つ社員には貸さない（期限の比較はここで直接行う）。"""
    item_code = request.form.get("item_code", "").strip()
    employee_no = request.form.get("employee_no", "").strip()
    try:
        lent_on, due_on = service.check_lendable(item_code, employee_no, request.form.get("lent_on", "").strip())
        for loan in repo.open_loans_of_employee(employee_no):
            if clock.today() > datetime.date.fromisoformat(loan["due_on"]):
                raise service.Rejected("返却の期限を過ぎた貸出があるため貸せません")
        service.check_limit(employee_no)
        service.register_loan(item_code, employee_no, lent_on, due_on)
    except service.Rejected as e:
        return _page(str(e), 400)
    return redirect("/carts/")


@bp.route("/return", methods=["POST"])
@staff_required
def return_():
    return _run(service.return_item, request.form.get("item_code", ""))


@bp.route("/history")
@login_required
def history():
    return render_template("carts/history.html", rows=repo.history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": [
        {"code": r["code"], "name": r["name"], "status": r["status"], "borrower": r["borrower"],
         "lent_on": r["lent_on"], "due_on": r["due_on"]}
        for r in service.status_list()
    ]})

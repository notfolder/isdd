"""安全ベストの貸出の画面と URL。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.safety_vests.models import RuleError, VestLoans

bp = Blueprint("safety_vests", __name__, url_prefix="/safety_vests", template_folder="templates")
loans = VestLoans()


def _page(error=None, status=200):
    q = request.values.get("q", "")
    return render_template("safety_vests/index.html", items=loans.list_items(q), q=q, error=error), status


def _run(action, operation):
    """きまりに反すれば 400 と理由を返す。成功すれば操作を記録して一覧へ戻す。"""
    try:
        target = operation()
    except RuleError as e:
        get_db().rollback()
        return _page(str(e), 400)
    audit.record("safety_vests", action, target)
    get_db().commit()
    return redirect(url_for("safety_vests.index"))


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_new():
    return _run("item_create", lambda: loans.create_item(request.form.get("code"), request.form.get("name")))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_edit():
    return _run("item_update", lambda: loans.update_item(request.form.get("code"), request.form.get("name")))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _run("item_delete", lambda: loans.delete_item(request.form.get("code")))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    f = request.form
    return _run("lend", lambda: loans.lend(f.get("item_code"), f.get("employee_no"), f.get("lent_on")))


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    return _run("return", lambda: loans.return_item(request.form.get("item_code")))


@bp.route("/history")
@login_required
def history():
    return render_template("safety_vests/history.html", rows=loans.history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": [
        {"code": i["code"], "name": i["name"], "status": i["status"], "borrower": i["borrower"],
         "lent_on": i["lent_on"], "due_on": i["due_on"]}
        for i in loans.list_items()
    ]})

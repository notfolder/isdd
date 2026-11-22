"""来客用入館証の貸出の画面。判定は domain.py に任せ、例外を受けて 400 にする。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core.auth import login_required, staff_required
from app.modules.guest_badges import domain

bp = Blueprint("guest_badges", __name__, url_prefix="/guest_badges", template_folder="templates")


def _page(error=None, status=200):
    html = render_template("guest_badges/index.html", rows=domain.list_items(request.args.get("q", "")), error=error)
    return html, status


def _act(action, *args):
    """操作を実行し、きまりに合わなければ 400、成功なら一覧へ。"""
    try:
        action(*args)
    except domain.RuleError as exc:
        return _page(str(exc), 400)
    return redirect("/guest_badges/")


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_new():
    return _act(domain.create_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_edit():
    return _act(domain.update_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _act(domain.delete_item, request.form.get("code"))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    return _act(domain.lend, request.form.get("item_code"), request.form.get("employee_no"), request.form.get("lent_on"))


@bp.route("/return", methods=["POST"])
@staff_required
def give_back():
    return _act(domain.give_back, request.form.get("item_code"))


@bp.route("/history")
@login_required
def history():
    return render_template("guest_badges/history.html", rows=domain.list_history())


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
        for r in domain.list_items()
    ]
    return jsonify({"items": items})

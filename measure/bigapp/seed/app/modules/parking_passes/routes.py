"""駐車許可証の貸出の画面。判定は service.py に任せる。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core.auth import login_required, staff_required
from app.modules.parking_passes import repo, service

bp = Blueprint("parking_passes", __name__, url_prefix="/parking_passes", template_folder="templates")

STATUS_LABELS = {"free": "貸出可", "lent": "貸出中", "overdue": "延滞"}


def _page(error=None, status=200):
    q = request.args.get("q", "").strip()
    html = render_template(
        "parking_passes/index.html", rows=service.status_rows(q), q=q, error=error, labels=STATUS_LABELS
    )
    return html, status


def _act(action, *args):
    try:
        action(*args)
    except service.RejectedError as e:
        return _page(str(e), 400)
    return redirect("/parking_passes/")


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_new():
    return _act(service.create_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_edit():
    return _act(service.update_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _act(service.delete_item, request.form.get("code"))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    f = request.form
    return _act(service.lend, f.get("item_code"), f.get("employee_no"), f.get("lent_on"))


@bp.route("/return", methods=["POST"])
@staff_required
def return_():
    return _act(service.return_item, request.form.get("item_code"))


@bp.route("/history")
@login_required
def history():
    return render_template("parking_passes/history.html", rows=repo.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    keys = ("code", "name", "status", "borrower", "lent_on", "due_on")
    return jsonify({"items": [{k: r[k] for k in keys} for r in service.status_rows()]})

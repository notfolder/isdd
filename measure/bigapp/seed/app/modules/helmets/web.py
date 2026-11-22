"""ヘルメット貸出の画面。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.helmets import domain

bp = Blueprint("helmets", __name__, url_prefix="/helmets", template_folder="templates")


def _render_index(error=None, status=200):
    items = domain.list_items(request.values.get("q", ""))
    return render_template("helmets/index.html", items=items, error=error, q=request.values.get("q", "")), status


def _apply(action, func, *args):
    """判定を実行し、成功なら記録して一覧へ、受け付けないときは 400。"""
    try:
        target = func(*args)
    except domain.HelmetError as e:
        get_db().rollback()
        return _render_index(error=str(e), status=400)
    audit.record("helmets", action, target)
    get_db().commit()
    return redirect("/helmets/")


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    f = request.form
    return _apply("item_create", domain.create_item, f.get("code"), f.get("name"))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    f = request.form
    return _apply("item_update", domain.update_item, f.get("code"), f.get("name"))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _apply("item_delete", domain.delete_item, request.form.get("code"))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    f = request.form
    return _apply("lend", domain.lend, f.get("item_code"), f.get("employee_no"), f.get("lent_on"))


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    return _apply("return", domain.return_item, request.form.get("item_code"))


@bp.route("/history")
@login_required
def history():
    return render_template("helmets/history.html", rows=domain.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {
            "code": i["code"],
            "name": i["name"],
            "status": i["status"],
            "borrower": i["borrower"],
            "lent_on": i["lent_on"],
            "due_on": i["due_on"],
        }
        for i in domain.list_items()
    ]
    return jsonify({"items": items})

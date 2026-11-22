"""社用車の貸出の画面。判定は service、SQL は repo に任せる。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.vehicles import bp, repo, service


def _index(error=None, status=200):
    keyword = request.args.get("q", "").strip()
    items = service.items_for_screen(keyword)
    return render_template("vehicles/index.html", items=items, q=keyword, error=error), status


def _run(action, *args):
    """処理を実行し、成功なら一覧へ、受け付けないなら 400 と理由を返す。"""
    try:
        action(*args)
    except ValueError as exc:
        get_db().rollback()
        return _index(str(exc), 400)
    get_db().commit()
    return redirect(url_for("vehicles.index"))


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    return _run(service.create_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    return _run(service.update_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _run(service.delete_item, request.form.get("code"))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    form = request.form
    return _run(service.lend, form.get("item_code"), form.get("employee_no"), form.get("lent_on"))


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    return _run(service.return_item, request.form.get("item_code"))


@bp.route("/history")
@login_required
def history():
    return render_template("vehicles/history.html", rows=repo.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": service.status_rows()})

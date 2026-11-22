"""カメラの貸出の画面と URL。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.cameras.models import CameraError, CameraRules

bp = Blueprint("cameras", __name__, url_prefix="/cameras", template_folder="templates")
rules = CameraRules()


def _page(error=None, status=200):
    q = request.values.get("q", "").strip()
    return render_template("cameras/index.html", items=rules.items(q), q=q, error=error), status


def _run(action, operation, *args):
    """判定と更新を行い、記録を 1 行残して一覧へ戻る。受け付けないときは 400。"""
    try:
        target = operation(*args)
    except CameraError as e:
        get_db().rollback()
        return _page(str(e), 400)
    audit.record("cameras", action, target)
    get_db().commit()
    return redirect(url_for("cameras.index"))


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    f = request.form
    return _run("item_create", rules.create_item, f.get("code"), f.get("name"))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    f = request.form
    return _run("item_update", rules.update_item, f.get("code"), f.get("name"))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _run("item_delete", rules.delete_item, request.form.get("code"))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    f = request.form
    return _run("lend", rules.lend, f.get("item_code"), f.get("employee_no"), f.get("lent_on"))


@bp.route("/return", methods=["POST"])
@staff_required
def give_back():
    return _run("return", rules.give_back, request.form.get("item_code"))


@bp.route("/history")
@login_required
def history():
    return render_template("cameras/history.html", rows=rules.history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": rules.items()})

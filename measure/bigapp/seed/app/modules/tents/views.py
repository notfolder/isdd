"""テントの貸出の画面と操作。"""

from flask import jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.tents import bp
from app.modules.tents.models import LendingError, TentLending

lending = TentLending()


def _index(error=None, status=200):
    q = request.args.get("q", "").strip()
    return render_template("tents/index.html", items=lending.items(q), q=q, error=error), status


def _run(action, operation, *args):
    """操作を実行して記録する。受け付けないときは 400 で理由を出す。"""
    try:
        target = operation(*args)
    except LendingError as e:
        get_db().rollback()
        return _index(str(e), 400)
    audit.record("tents", action, target)
    get_db().commit()
    return redirect("/tents/")


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    return _run("item_create", lending.create_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    return _run("item_update", lending.update_item, request.form.get("code"), request.form.get("name"))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _run("item_delete", lending.delete_item, request.form.get("code"))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    f = request.form
    return _run("lend", lending.lend, f.get("item_code"), f.get("employee_no"), f.get("lent_on"))


@bp.route("/return", methods=["POST"])
@staff_required
def give_back():
    return _run("return", lending.give_back, request.form.get("item_code"))


@bp.route("/history")
@login_required
def history():
    return render_template("tents/history.html", rows=lending.history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": [
        {"code": i["code"], "name": i["name"], "status": i["status"], "borrower": i["borrower"],
         "lent_on": i["lent_on"], "due_on": i["due_on"]}
        for i in lending.items()
    ]})

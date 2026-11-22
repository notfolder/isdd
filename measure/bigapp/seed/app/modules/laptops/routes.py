"""ノート PC の貸出の画面。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core.auth import login_required, staff_required
from app.modules.laptops import bp, service


def _page(error=None, status=200):
    q = request.args.get("q", "")
    return render_template("laptops/index.html", items=service.items(q), q=q, error=error), status


def _act(func, *args):
    """処理を行い、成功なら一覧へ、受け付けなければ 400 で理由を出す。"""
    try:
        func(*args)
    except service.Rejected as e:
        return _page(str(e), 400)
    return redirect(url_for("laptops.index"))


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
def give_back():
    return _act(service.give_back, request.form.get("item_code"))


@bp.route("/history")
@login_required
def history():
    return render_template("laptops/history.html", rows=service.history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": service.status_items()})

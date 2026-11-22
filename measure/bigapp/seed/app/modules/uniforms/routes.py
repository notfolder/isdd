"""制服の貸与の画面。判定は service.py に任せ、ここは入力と表示だけを扱う。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.uniforms import repo, service
from app.modules.uniforms.service import ServiceError

bp = Blueprint("uniforms", __name__, url_prefix="/uniforms", template_folder="templates")


def _render_index(error=None, status=200):
    query = request.values.get("q", "").strip()
    rows = service.status_rows(query)
    return render_template("uniforms/index.html", rows=rows, q=query, error=error), status


def _run(action, *args):
    """処理を実行する。受け付けないときは 400 で理由を出し、データは変えない。"""
    try:
        action(*args)
    except ServiceError as e:
        get_db().rollback()
        return _render_index(str(e), 400)
    get_db().commit()
    return redirect("/uniforms/")


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_new():
    form = request.form
    return _run(service.create_item, form.get("code", ""), form.get("name", ""))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_edit():
    form = request.form
    return _run(service.update_item, form.get("code", ""), form.get("name", ""))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _run(service.delete_item, request.form.get("code", ""))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    form = request.form
    return _run(service.lend, form.get("item_code", ""), form.get("employee_no", ""), form.get("lent_on", ""))


@bp.route("/return", methods=["POST"])
@staff_required
def return_():
    return _run(service.return_item, request.form.get("item_code", ""))


@bp.route("/history")
@login_required
def history():
    return render_template("uniforms/history.html", rows=repo.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {
            "code": row["code"],
            "name": row["name"],
            "status": status,
            "borrower": row["borrower"],
            "lent_on": row["lent_on"],
            "due_on": row["due_on"],
        }
        for row, status in service.status_rows()
    ]
    return jsonify({"items": items})

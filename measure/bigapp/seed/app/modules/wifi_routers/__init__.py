"""モバイル Wi-Fi の貸出。画面と URL。判定と更新は logic.py。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core.auth import login_required, staff_required
from app.modules.wifi_routers import logic

TITLE = "モバイル Wi-Fi の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS wifi_routers_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS wifi_routers_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("wifi_routers", __name__, url_prefix="/wifi_routers", template_folder="templates")


def _render_index(error=None, status=200):
    q = request.args.get("q", "")
    return render_template("wifi_routers/index.html", items=logic.list_items(q), q=q, error=error), status


def _act(func, *args):
    """操作を実行する。きまりに合わなければ 400 で理由を出し、成功なら一覧へ戻す。"""
    try:
        func(*args)
    except logic.RuleError as e:
        return _render_index(str(e), 400)
    return redirect(url_for("wifi_routers.index"))


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    return _act(logic.create_item, request.form.get("code", ""), request.form.get("name", ""))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    return _act(logic.update_item, request.form.get("code", ""), request.form.get("name", ""))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _act(logic.delete_item, request.form.get("code", ""))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    form = request.form
    return _act(logic.lend, form.get("item_code", ""), form.get("employee_no", ""), form.get("lent_on", ""))


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    return _act(logic.return_item, request.form.get("item_code", ""))


@bp.route("/history")
@login_required
def history():
    return render_template("wifi_routers/history.html", rows=logic.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(
        {
            "items": [
                {"code": i.code, "name": i.name, "status": i.status, "borrower": i.borrower, "lent_on": i.lent_on, "due_on": i.due_on}
                for i in logic.list_items()
            ]
        }
    )

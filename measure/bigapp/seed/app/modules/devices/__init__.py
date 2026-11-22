"""モバイル機器の貸出（総務規程 第 3 条・第 6 条）の画面。"""

from dataclasses import asdict

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.devices import logic

TITLE = "モバイル機器の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS devices_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("devices", __name__, url_prefix="/devices", template_folder="templates")


def _page(error=None, status=200):
    q = request.values.get("q", "").strip() if request.method == "GET" else ""
    items = logic.list_status(get_db(), q)
    return render_template("devices/index.html", items=items, q=q, error=error), status


def _run(action, target_of, operation):
    """操作を実行し、記録を残して一覧へ戻す。きまりに合わなければ 400 で理由を出す。"""
    conn = get_db()
    try:
        result = operation(conn)
    except logic.RuleError as e:
        conn.rollback()
        return _page(str(e), 400)
    audit.record("devices", action, target_of(result))
    conn.commit()
    return redirect("/devices/")


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    f = request.form
    return _run("item_create", lambda r: r.code, lambda c: logic.create_item(c, f.get("code", ""), f.get("name", "")))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    f = request.form
    return _run("item_update", lambda r: r.code, lambda c: logic.update_item(c, f.get("code", ""), f.get("name", "")))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _run("item_delete", lambda r: r.code, lambda c: logic.delete_item(c, request.form.get("code", "")))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    f = request.form
    return _run(
        "lend",
        lambda r: f"{r.item_code}:{r.employee_no}",
        lambda c: logic.lend(c, f.get("item_code", ""), f.get("employee_no", ""), f.get("lent_on", "")),
    )


@bp.route("/return", methods=["POST"])
@staff_required
def return_():
    return _run("return", lambda r: r.code, lambda c: logic.return_item(c, request.form.get("item_code", "")))


@bp.route("/history")
@login_required
def history():
    return render_template("devices/history.html", rows=logic.list_history(get_db()))


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": [asdict(s) for s in logic.list_status(get_db())]})

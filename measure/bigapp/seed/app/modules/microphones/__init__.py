"""マイクの貸出。画面と URL をここに置き、判定と処理は logic.py に置く。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.microphones import logic

TITLE = "マイクの貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS microphones_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS microphones_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("microphones", __name__, url_prefix="/microphones", template_folder="templates")


def _page(error=None, status=200):
    items = logic.list_items(get_db(), request.args.get("q", ""))
    return render_template("microphones/index.html", items=items, q=request.args.get("q", ""), error=error), status


def _act(action, operation):
    """POST の共通の流れ。成功なら記録して一覧へ、きまりに合わなければ 400。"""
    db = get_db()
    try:
        target = operation(db)
    except logic.RuleError as e:
        db.rollback()
        return _page(error=str(e), status=400)
    audit.record("microphones", action, target)
    db.commit()
    return redirect("/microphones/")


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    f = request.form
    return _act("item_create", lambda db: logic.create_item(db, f.get("code", ""), f.get("name", "")))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    f = request.form
    return _act("item_update", lambda db: logic.update_item(db, f.get("code", ""), f.get("name", "")))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _act("item_delete", lambda db: logic.delete_item(db, request.form.get("code", "")))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    f = request.form
    return _act("lend", lambda db: logic.lend(db, f.get("item_code", ""), f.get("employee_no", ""), f.get("lent_on", "")))


@bp.route("/return", methods=["POST"])
@staff_required
def give_back():
    return _act("return", lambda db: logic.give_back(db, request.form.get("item_code", "")))


@bp.route("/history")
@login_required
def history():
    return render_template("microphones/history.html", loans=logic.list_history(get_db()))


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": [i.as_json() for i in logic.list_items(get_db())]})

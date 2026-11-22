"""書籍の貸出の画面とルート。判定は models.BookRules に任せる。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.books import bp
from app.modules.books.models import BookRules, RuleError

rules = BookRules()


def _page(error=None, status=200):
    q = request.values.get("q", "").strip()
    return render_template("books/index.html", rows=rules.list_items(q), q=q, error=error), status


def _change(action, target, operation):
    """データを変える操作の共通の流れ。受け付けなければ 400、成功すれば記録を 1 行残して一覧へ。"""
    try:
        operation()
    except RuleError as e:
        get_db().rollback()
        return _page(str(e), 400)
    audit.record("books", action, target)
    get_db().commit()
    return redirect(url_for("books.index"))


def _form(name):
    return request.form.get(name, "").strip()


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code, name = _form("code"), _form("name")
    return _change("item_create", code, lambda: rules.create_item(code, name))


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code, name = _form("code"), _form("name")
    return _change("item_update", code, lambda: rules.update_item(code, name))


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = _form("code")
    return _change("item_delete", code, lambda: rules.delete_item(code))


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    code, employee_no, lent_on = _form("item_code"), _form("employee_no"), _form("lent_on")
    return _change("lend", f"{code} -> {employee_no}", lambda: rules.lend(code, employee_no, lent_on))


@bp.route("/return", methods=["POST"])
@staff_required
def give_back():
    code = _form("item_code")
    return _change("return", code, lambda: rules.give_back(code))


@bp.route("/history")
@login_required
def history():
    return render_template("books/history.html", rows=rules.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {
            "code": r["code"],
            "name": r["name"],
            "status": r["status"],
            "borrower": r["borrower"],
            "lent_on": r["lent_on"],
            "due_on": r["due_on"],
        }
        for r in rules.list_items()
    ]
    return jsonify({"items": items})

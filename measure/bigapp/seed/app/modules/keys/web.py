"""鍵の貸出の画面。判定は domain.py、ここは入力の受け取りと表示だけ。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.keys import bp, domain


def _page(error=None, status=200):
    items = domain.list_items(request.args.get("q", ""))
    return render_template("keys/index.html", items=items, error=error, q=request.args.get("q", "")), status


def _change(action, func, *fields):
    """データを変える操作の共通の流れ。成功なら記録して一覧へ、受け付けないなら 400。"""
    try:
        target = func(*(request.form.get(f) for f in fields))
    except domain.RejectedError as exc:
        get_db().rollback()
        return _page(str(exc), 400)
    audit.record("keys", action, target)
    get_db().commit()
    return redirect(url_for("keys.index"))


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    return _change("item_create", domain.create_item, "code", "name")


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    return _change("item_update", domain.update_item, "code", "name")


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    return _change("item_delete", domain.delete_item, "code")


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    return _change("lend", domain.lend, "item_code", "employee_no", "lent_on")


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    return _change("return", domain.return_item, "item_code")


@bp.route("/history")
@login_required
def history():
    return render_template("keys/history.html", rows=domain.list_history())


@bp.route("/status.json")
@login_required
def status_json():
    items = []
    for row in domain.list_items():
        status = {None: "free", "lent": "lent", "overdue": "overdue"}[row["state"]]
        items.append(
            {
                "code": row["code"],
                "name": row["name"],
                "status": status,
                "borrower": row["employee_no"],
                "lent_on": row["lent_on"],
                "due_on": row["due_on"],
            }
        )
    return jsonify({"items": items})

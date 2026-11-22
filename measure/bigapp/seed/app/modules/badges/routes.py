"""社章の申請の画面。判定は service.py に任せる。"""

from flask import abort, jsonify, redirect, render_template, request, url_for

from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.badges import bp, service


def _index(state, error=None, status=200):
    try:
        rows = service.list_for_screen(state)
    except service.Rejected as exc:
        rows, error, status = service.list_for_screen(None), str(exc), 400
    return render_template(
        "badges/index.html", rows=rows, error=error, state=state or "", states=service.STATE_LABELS
    ), status


def _done(action):
    """処理を実行して commit し、一覧へ戻す。受け付けないときは 400 で理由を出す。"""
    conn = get_db()
    try:
        action()
    except service.Rejected as exc:
        conn.rollback()
        return _index(None, str(exc), 400)
    conn.commit()
    return redirect(url_for("badges.index"))


@bp.route("/")
@login_required
def index():
    return _index(request.args.get("state", "").strip())


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    return _done(lambda: service.apply(form.get("employee_no"), form.get("quantity"), form.get("unit_price")))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return _done(lambda: service.approve(request.form.get("request_id"), current_user()["employee_no"]))


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _done(lambda: service.reject(request.form.get("request_id")))


@bp.route("/detail")
@login_required
def detail():
    try:
        row = service.show(request.args.get("request_id"))
    except service.Rejected:
        abort(404)
    return render_template("badges/detail.html", r=row, states=service.STATE_LABELS)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"requests": [
        {"id": r["id"], "employee": r["employee_no"], "quantity": r["quantity"],
         "unit_price": r["unit_price"], "amount_incl_tax": r["amount_incl_tax"], "state": r["state"]}
        for r in service.list_for_screen(None)
    ]})

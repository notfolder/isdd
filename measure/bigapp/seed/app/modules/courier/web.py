"""宅配便の申請の画面。判定は domain.py に任せ、例外を受けて 400 で返す。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.courier import domain

bp = Blueprint("courier", __name__, url_prefix="/courier", template_folder="templates")

STATE_LABELS = {"pending": "申請中", "approved": "承認", "rejected": "却下"}


def _page(error=None, status=200):
    """一覧の画面を作る。state が不正なら全件を出してエラーを表示する。"""
    state = request.args.get("state", "").strip()
    try:
        rows = domain.list_requests(state or None)
    except domain.CourierError as exc:
        error, status, state = str(exc), 400, ""
        rows = domain.list_requests()
    return render_template(
        "courier/index.html", rows=rows, state=state, error=error, labels=STATE_LABELS
    ), status


def _fail(exc):
    return _page(error=str(exc), status=400)


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    try:
        new_id = domain.apply(form.get("employee_no"), form.get("quantity"), form.get("unit_price"))
    except domain.CourierError as exc:
        return _fail(exc)
    audit.record("courier", "apply", str(new_id))
    get_db().commit()
    return redirect("/courier/")


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    try:
        target = domain.approve(request.form.get("request_id"), current_user()["employee_no"])
    except domain.CourierError as exc:
        return _fail(exc)
    audit.record("courier", "approve", str(target))
    get_db().commit()
    return redirect("/courier/")


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    try:
        target = domain.reject(request.form.get("request_id"))
    except domain.CourierError as exc:
        return _fail(exc)
    audit.record("courier", "reject", str(target))
    get_db().commit()
    return redirect("/courier/")


@bp.route("/detail")
@login_required
def detail():
    try:
        row = domain.get_request(request.args.get("request_id"))
    except domain.CourierError as exc:
        return render_template("courier/detail.html", row=None, error=str(exc), labels=STATE_LABELS), 404
    employee = get_db().execute("SELECT name FROM employees WHERE employee_no = ?", (row["employee_no"],)).fetchone()
    subtotal = row["quantity"] * row["unit_price"]
    return render_template(
        "courier/detail.html", row=row, error=None, labels=STATE_LABELS, subtotal=subtotal,
        employee_name=employee["name"] if employee else "",
    )


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"requests": [
        {
            "id": r["id"],
            "employee": r["employee_no"],
            "quantity": r["quantity"],
            "unit_price": r["unit_price"],
            "amount_incl_tax": r["amount_incl_tax"],
            "state": r["state"],
        }
        for r in domain.list_requests()
    ]})

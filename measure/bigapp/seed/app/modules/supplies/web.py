"""消耗品の申請の画面。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.supplies import domain

bp = Blueprint("supplies", __name__, url_prefix="/supplies", template_folder="templates")

STATES = ("pending", "approved", "rejected")


def _requests(state=None):
    sql = (
        "SELECT r.*, e.name AS employee_name FROM supplies_requests r "
        "JOIN employees e ON e.employee_no = r.employee_no"
    )
    params = ()
    if state in STATES:
        sql += " WHERE r.state = ?"
        params = (state,)
    return get_db().execute(sql + " ORDER BY r.id", params).fetchall()


def _page(error=None, status=200):
    state = request.args.get("state", "")
    html = render_template("supplies/index.html", rows=_requests(state), state=state, error=error)
    return html, status


def _fail(error):
    """受け付けないときは 400 で理由を出す。データは変えない。"""
    get_db().rollback()
    return _page(error, 400)


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    try:
        new_id = domain.apply(
            request.form.get("employee_no", "").strip(),
            request.form.get("quantity"),
            request.form.get("unit_price"),
        )
    except domain.SuppliesError as e:
        return _fail(str(e))
    audit.record("supplies", "apply", str(new_id))
    get_db().commit()
    return redirect("/supplies/")


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    try:
        target = domain.approve(request.form.get("request_id"), current_user()["employee_no"])
    except domain.SuppliesError as e:
        return _fail(str(e))
    audit.record("supplies", "approve", str(target))
    get_db().commit()
    return redirect("/supplies/")


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    try:
        target = domain.reject(request.form.get("request_id"))
    except domain.SuppliesError as e:
        return _fail(str(e))
    audit.record("supplies", "reject", str(target))
    get_db().commit()
    return redirect("/supplies/")


@bp.route("/detail")
@login_required
def detail():
    try:
        row = domain.find_request(request.args.get("request_id"))
    except domain.SuppliesError as e:
        return _fail(str(e))
    employee = get_db().execute("SELECT name FROM employees WHERE employee_no = ?", (row["employee_no"],)).fetchone()
    return render_template("supplies/detail.html", r=row, employee_name=employee["name"])


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(
        {
            "requests": [
                {
                    "id": r["id"],
                    "employee": r["employee_no"],
                    "quantity": r["quantity"],
                    "unit_price": r["unit_price"],
                    "amount_incl_tax": r["amount_incl_tax"],
                    "state": r["state"],
                }
                for r in _requests()
            ]
        }
    )

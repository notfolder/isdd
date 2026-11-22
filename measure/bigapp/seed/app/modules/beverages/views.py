"""来客用飲料の申請の画面と操作。"""

from flask import Blueprint, abort, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.beverages.models import (
    APPROVED,
    PENDING,
    QUANTITY_RANGE,
    REJECTED,
    STATES,
    UNIT_PRICE_RANGE,
    BeverageRules,
    with_tax,
)

bp = Blueprint("beverages", __name__, url_prefix="/beverages", template_folder="templates")


def _rows(state=None):
    sql = (
        "SELECT r.*, e.name AS employee_name FROM beverages_requests r "
        "JOIN employees e ON e.employee_no = r.employee_no"
    )
    args = ()
    if state:
        sql += " WHERE r.state = ?"
        args = (state,)
    return get_db().execute(sql + " ORDER BY r.id", args).fetchall()


def _index(error=None, status=200):
    state = request.args.get("state", "")
    rows = _rows(state if state in STATES else None)
    return render_template("beverages/index.html", rows=rows, error=error, state=state, states=STATES), status


def _get_request(request_id):
    text = (request_id or "").strip()
    if not (text.isascii() and text.isdigit()):
        return None
    return get_db().execute("SELECT * FROM beverages_requests WHERE id = ?", (int(text),)).fetchone()


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    conn = get_db()
    number = form.get("employee_no", "").strip()
    employee = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
    error = BeverageRules.check_employee(employee)
    quantity = unit_price = None
    if not error:
        quantity, error = BeverageRules.parse_int(form.get("quantity"), *QUANTITY_RANGE, "数量")
    if not error:
        unit_price, error = BeverageRules.parse_int(form.get("unit_price"), *UNIT_PRICE_RANGE, "単価")
    if error:
        return _index(error, 400)
    cur = conn.execute(
        "INSERT INTO beverages_requests (employee_no, quantity, unit_price, amount_incl_tax, state) VALUES (?, ?, ?, ?, ?)",
        (number, quantity, unit_price, with_tax(quantity, unit_price), PENDING),
    )
    audit.record("beverages", "apply", str(cur.lastrowid))
    conn.commit()
    return redirect("/beverages/")


def _decide(action, new_state, check):
    conn = get_db()
    row = _get_request(request.form.get("request_id"))
    error = check(row)
    if error:
        return _index(error, 400)
    conn.execute("UPDATE beverages_requests SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("beverages", action, str(row["id"]))
    conn.commit()
    return redirect("/beverages/")


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    approver_no = current_user()["employee_no"]
    return _decide("approve", APPROVED, lambda row: BeverageRules.check_approver(row, approver_no))


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _decide("reject", REJECTED, BeverageRules.check_decidable)


@bp.route("/detail")
@login_required
def detail():
    row = _get_request(request.args.get("request_id"))
    if row is None:
        abort(404)
    employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (row["employee_no"],)).fetchone()
    return render_template("beverages/detail.html", r=row, employee=employee)


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
                for r in _rows()
            ]
        }
    )

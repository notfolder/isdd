"""ケータリング申請の画面と操作。"""

import math

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.catering.models import STATES, CateringRules

bp = Blueprint("catering", __name__, url_prefix="/catering", template_folder="templates")


def _rows(state=None):
    sql = (
        "SELECT r.*, e.name AS employee_name FROM catering_requests r "
        "LEFT JOIN employees e ON e.employee_no = r.employee_no"
    )
    if state in STATES:
        return get_db().execute(sql + " WHERE r.state = ? ORDER BY r.id", (state,)).fetchall()
    return get_db().execute(sql + " ORDER BY r.id").fetchall()


def _fail(message, state=None):
    """受け付けない。データは変えず、理由を付けて 400 を返す。"""
    return render_template("catering/index.html", rows=_rows(state), error=message, state=state or "", states=STATES), 400


def _get_request(raw_id):
    try:
        request_id = int(raw_id)
    except (TypeError, ValueError):
        return None
    return get_db().execute("SELECT * FROM catering_requests WHERE id = ?", (request_id,)).fetchone()


@bp.route("/")
@login_required
def index():
    state = request.args.get("state", "")
    return render_template("catering/index.html", rows=_rows(state), error=None, state=state, states=STATES)


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (form.get("employee_no", "").strip(),)).fetchone()
    error = CateringRules.check_applicant(employee)
    if error:
        return _fail(error)
    quantity = CateringRules.parse_quantity(form.get("quantity"))
    if quantity is None:
        return _fail("数量は 1 以上 200 以下の整数で入力してください")
    unit_price = CateringRules.parse_unit_price(form.get("unit_price"))
    if unit_price is None:
        return _fail("単価は 1 以上 100000 以下の整数（円）で入力してください")

    # 税込みの金額は、消費税 10% を足して 1 円未満を切り捨てる
    amount = math.floor(quantity * unit_price * 1.1)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO catering_requests (employee_no, quantity, unit_price, amount_incl_tax, state, requested_on) "
        "VALUES (?, ?, ?, ?, 'pending', ?)",
        (employee["employee_no"], quantity, unit_price, amount, clock.today().isoformat()),
    )
    audit.record("catering", "apply", str(cur.lastrowid))
    conn.commit()
    return redirect(url_for("catering.index"))


def _decide(action, new_state):
    row = _get_request(request.form.get("request_id"))
    if action == "approve":
        error = CateringRules.check_approve(row, current_user()["employee_no"])
    else:
        error = CateringRules.check_decidable(row)
    if error:
        return _fail(error)
    conn = get_db()
    conn.execute("UPDATE catering_requests SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("catering", action, str(row["id"]))
    conn.commit()
    return redirect(url_for("catering.index"))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return _decide("approve", "approved")


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _decide("reject", "rejected")


@bp.route("/detail")
@login_required
def detail():
    row = _get_request(request.args.get("request_id"))
    if row is None:
        return render_template("catering/index.html", rows=_rows(), error="申請が見つかりません", state="", states=STATES), 404
    employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (row["employee_no"],)).fetchone()
    return render_template("catering/detail.html", r=row, employee=employee)


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

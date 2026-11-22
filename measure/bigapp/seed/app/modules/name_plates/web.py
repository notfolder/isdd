"""名札の申請の画面。"""

from flask import abort, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db

from . import bp, domain
from .domain import RequestError


def _rows(state=None):
    sql = (
        "SELECT r.*, e.name AS employee_name FROM name_plates_requests r "
        "LEFT JOIN employees e ON e.employee_no = r.employee_no"
    )
    args = ()
    if state:
        sql += " WHERE r.state = ?"
        args = (state,)
    items = []
    for r in get_db().execute(sql + " ORDER BY r.id", args).fetchall():
        d = dict(r)
        d["net"] = domain.net_amount(r["quantity"], r["unit_price"])
        d["gross"] = domain.gross_amount(r["quantity"], r["unit_price"])
        items.append(d)
    return items


def _page(error=None, status=200, state=""):
    return render_template("name_plates/index.html", rows=_rows(state or None), error=error, state=state), status


def _get_request(request_id):
    text = (request_id or "").strip()
    if not text.isascii() or not text.isdigit():
        return None
    return get_db().execute("SELECT * FROM name_plates_requests WHERE id = ?", (int(text),)).fetchone()


@bp.route("/")
@login_required
def index():
    state = request.args.get("state", "").strip()
    if state and state not in domain.STATES:
        return _page("状態が正しくありません", 400)
    return _page(state=state)


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    number = request.form.get("employee_no", "").strip()
    try:
        employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
        domain.check_applicant(employee)
        quantity = domain.parse_int(request.form.get("quantity"), "数量", domain.QUANTITY_MIN, domain.QUANTITY_MAX)
        price = domain.parse_int(request.form.get("unit_price"), "単価", domain.PRICE_MIN, domain.PRICE_MAX)
    except RequestError as e:
        return _page(str(e), 400)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO name_plates_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, 'pending')",
        (number, quantity, price),
    )
    audit.record("name_plates", "apply", str(cur.lastrowid))
    conn.commit()
    return redirect(url_for("name_plates.index"))


def _decide(action, new_state):
    row = _get_request(request.form.get("request_id"))
    try:
        domain.check_decidable(row, current_user()["employee_no"], approving=(action == "approve"))
    except RequestError as e:
        return _page(str(e), 400)
    conn = get_db()
    conn.execute("UPDATE name_plates_requests SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("name_plates", action, str(row["id"]))
    conn.commit()
    return redirect(url_for("name_plates.index"))


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
        abort(404)
    item = next(r for r in _rows() if r["id"] == row["id"])
    return render_template("name_plates/detail.html", r=item)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({
        "requests": [
            {"id": r["id"], "employee": r["employee_no"], "quantity": r["quantity"],
             "unit_price": r["unit_price"], "amount_incl_tax": r["gross"], "state": r["state"]}
            for r in _rows()
        ]
    })

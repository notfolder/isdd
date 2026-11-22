"""文具の申請の画面。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.stationery import bp, queries, rules


def _view_rows(state=None):
    """一覧に出す行。税込みの金額を足す。"""
    rows = []
    for r in queries.list_requests(state):
        item = dict(r)
        item["subtotal"] = rules.subtotal(r["quantity"], r["unit_price"])
        item["amount_incl_tax"] = rules.total(r["quantity"], r["unit_price"])
        rows.append(item)
    return rows


def _index(error=None, status=200):
    state = request.args.get("state", "")
    if state not in rules.STATES:
        state = ""
    return render_template("stationery/index.html", rows=_view_rows(state or None), state=state, states=rules.STATES, error=error), status


def _parse_id(text):
    return rules.parse_int(text, 1, 2**62)


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    employee_no = request.form.get("employee_no", "").strip()
    quantity, unit_price, error = rules.check_apply(
        queries.find_employee(employee_no), request.form.get("quantity"), request.form.get("unit_price")
    )
    if error:
        return _index(error, 400)
    new_id = queries.insert_request(employee_no, quantity, unit_price)
    audit.record("stationery", "apply", str(new_id))
    get_db().commit()
    return redirect(url_for("stationery.index"))


def _decide(action, new_state):
    request_id = _parse_id(request.form.get("request_id"))
    row = queries.get_request(request_id) if request_id is not None else None
    error = rules.check_decision(row, action, current_user()["employee_no"])
    if error:
        return _index(error, 400)
    queries.set_state(request_id, new_state)
    audit.record("stationery", action, str(request_id))
    get_db().commit()
    return redirect(url_for("stationery.index"))


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
    request_id = _parse_id(request.args.get("request_id"))
    row = queries.get_request(request_id) if request_id is not None else None
    if row is None:
        return render_template("stationery/detail.html", item=None, error="申請が見つかりません"), 404
    item = dict(row)
    item["subtotal"] = rules.subtotal(row["quantity"], row["unit_price"])
    item["amount_incl_tax"] = rules.total(row["quantity"], row["unit_price"])
    return render_template("stationery/detail.html", item=item, error=None)


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
                for r in _view_rows()
            ]
        }
    )

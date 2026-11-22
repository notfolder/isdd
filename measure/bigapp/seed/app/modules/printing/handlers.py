"""印刷の申請の画面。"""

from flask import abort, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.printing import bp, queries, rules

STATE_LABELS = {"pending": "申請中", "approved": "承認", "rejected": "却下"}


def _view_rows(rows):
    return [
        {
            "id": r["id"],
            "employee_no": r["employee_no"],
            "employee_name": queries.employee_name(r["employee_no"]),
            "quantity": r["quantity"],
            "unit_price": r["unit_price"],
            "amount": r["quantity"] * r["unit_price"],
            "amount_incl_tax": rules.with_tax(r["quantity"], r["unit_price"]),
            "state": r["state"],
            "state_label": STATE_LABELS.get(r["state"], r["state"]),
        }
        for r in rows
    ]


def _render_index(error=None, status=200):
    state = request.args.get("state", "").strip()
    rows = _view_rows(queries.list_requests(state or None))
    page = render_template(
        "printing/index.html", rows=rows, employees=queries.active_employees(), state=state, labels=STATE_LABELS, error=error
    )
    return page, status


def _reject_input(message):
    return _render_index(error=message, status=400)


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    employee_no = form.get("employee_no", "").strip()
    if queries.find_active_employee(employee_no) is None:
        return _reject_input("在籍している社員を指定してください")
    quantity = rules.parse_quantity(form.get("quantity"))
    if quantity is None:
        return _reject_input("数量は 1 以上 1000 以下の整数で入力してください")
    unit_price = rules.parse_unit_price(form.get("unit_price"))
    if unit_price is None:
        return _reject_input("単価は 1 以上 100000 以下の整数（円）で入力してください")
    request_id = queries.insert_request(employee_no, quantity, unit_price)
    audit.record("printing", "apply", str(request_id))
    get_db().commit()
    return redirect(url_for("printing.index"))


def _decide(action, new_state):
    """承認と却下に共通の処理。"""
    request_id = rules.parse_int(request.form.get("request_id"), 1, 2**62)
    row = queries.find_request(request_id) if request_id is not None else None
    if row is None:
        return _reject_input("申請が見つかりません")
    if not rules.can_decide(row["state"]):
        return _reject_input("申請中の申請だけ処理できます")
    if action == "approve" and rules.is_self_approval(row["employee_no"], current_user()["employee_no"]):
        return _reject_input("自分の申請は承認できません")
    queries.update_state(row["id"], new_state)
    audit.record("printing", action, str(row["id"]))
    get_db().commit()
    return redirect(url_for("printing.index"))


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
    request_id = rules.parse_int(request.args.get("request_id"), 1, 2**62)
    row = queries.find_request(request_id) if request_id is not None else None
    if row is None:
        abort(404)
    return render_template("printing/detail.html", r=_view_rows([row])[0])


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
                for r in _view_rows(queries.list_requests())
            ]
        }
    )

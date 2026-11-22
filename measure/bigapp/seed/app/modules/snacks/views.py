"""茶菓の申請の画面と操作。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.snacks import bp
from app.modules.snacks.models import STATES, SnackRules, parse_int

COLUMNS = "id, employee_no, quantity, unit_price, amount_incl_tax, state"


def _list(state=None):
    sql = f"SELECT {COLUMNS} FROM snacks_requests"
    args = ()
    if state:
        sql += " WHERE state = ?"
        args = (state,)
    return get_db().execute(sql + " ORDER BY id", args).fetchall()


def _page(error=None, status=200):
    state = request.args.get("state", "")
    return render_template("snacks/index.html", rows=_list(state if state in STATES else None), error=error, state=state), status


def _find(request_id):
    number = parse_int(request_id)
    if number is None:
        return None
    return get_db().execute(f"SELECT {COLUMNS} FROM snacks_requests WHERE id = ?", (number,)).fetchone()


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    conn = get_db()
    number = request.form.get("employee_no", "").strip()
    employee = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
    quantity, unit_price = parse_int(request.form.get("quantity")), parse_int(request.form.get("unit_price"))
    error = SnackRules.check_apply(employee, quantity, unit_price)
    if error:
        return _page(error, 400)
    # 税込みの金額は SQL の中で計算する（消費税 10%、1 円未満は切り捨て）
    cursor = conn.execute(
        "INSERT INTO snacks_requests (employee_no, quantity, unit_price, amount_incl_tax, state) "
        "VALUES (?, ?, ?, CAST(? * ? * 110 / 100 AS INTEGER), 'pending')",
        (number, quantity, unit_price, quantity, unit_price),
    )
    audit.record("snacks", "apply", str(cursor.lastrowid))
    conn.commit()
    return redirect(url_for("snacks.index"))


def _decide(action, new_state, check):
    conn = get_db()
    row = _find(request.form.get("request_id"))
    error = check(row)
    if error:
        return _page(error, 400)
    conn.execute("UPDATE snacks_requests SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("snacks", action, str(row["id"]))
    conn.commit()
    return redirect(url_for("snacks.index"))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return _decide("approve", "approved", lambda row: SnackRules.check_approve(row, current_user()))


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _decide("reject", "rejected", SnackRules.check_decide)


@bp.route("/detail")
@login_required
def detail():
    row = _find(request.args.get("request_id"))
    if row is None:
        return _page("申請が見つかりません", 400)
    employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (row["employee_no"],)).fetchone()
    return render_template("snacks/detail.html", row=row, employee=employee)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"requests": [
        {"id": r["id"], "employee": r["employee_no"], "quantity": r["quantity"],
         "unit_price": r["unit_price"], "amount_incl_tax": r["amount_incl_tax"], "state": r["state"]}
        for r in _list()
    ]})

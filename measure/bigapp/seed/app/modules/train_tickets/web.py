"""乗車券の申請の画面。"""

from flask import abort, jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.train_tickets import bp, domain


def _rows(state=None):
    sql = (
        "SELECT r.*, e.name AS employee_name FROM train_tickets_requests r "
        "JOIN employees e ON e.employee_no = r.employee_no"
    )
    params = ()
    if state:
        sql += " WHERE r.state = ?"
        params = (state,)
    rows = get_db().execute(sql + " ORDER BY r.id", params).fetchall()
    return [dict(r, amount_excl_tax=r["quantity"] * r["unit_price"], amount_incl_tax=domain.tax_included(r["quantity"], r["unit_price"])) for r in rows]


def _find(request_id):
    text = (request_id or "").strip()
    if not text.isascii() or not text.isdigit():
        return None
    return get_db().execute("SELECT * FROM train_tickets_requests WHERE id = ?", (int(text),)).fetchone()


def _page(error=None, status=200):
    state = request.args.get("state", "")
    if state not in domain.STATES:
        state = ""
    html = render_template("train_tickets/index.html", rows=_rows(state or None), state=state, states=domain.STATES, error=error)
    return html, status


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    conn = get_db()
    try:
        number = form.get("employee_no", "").strip()
        employee = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
        domain.check_employee(employee)
        quantity = domain.parse_int(form.get("quantity"), "数量", domain.QUANTITY_MIN, domain.QUANTITY_MAX)
        unit_price = domain.parse_int(form.get("unit_price"), "単価", domain.PRICE_MIN, domain.PRICE_MAX)
    except domain.RuleError as e:
        return _page(str(e), 400)
    cur = conn.execute(
        "INSERT INTO train_tickets_requests (employee_no, quantity, unit_price, state, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (number, quantity, unit_price, clock.now_text()),
    )
    audit.record("train_tickets", "apply", str(cur.lastrowid))
    conn.commit()
    return redirect(url_for("train_tickets.index"))


def _change_state(action, new_state):
    conn = get_db()
    row = _find(request.form.get("request_id"))
    try:
        if action == "approve":
            domain.check_can_approve(row, current_user()["employee_no"])
        else:
            domain.check_pending(row)
    except domain.RuleError as e:
        return _page(str(e), 400)
    conn.execute("UPDATE train_tickets_requests SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("train_tickets", action, str(row["id"]))
    conn.commit()
    return redirect(url_for("train_tickets.index"))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return _change_state("approve", "approved")


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _change_state("reject", "rejected")


@bp.route("/detail")
@login_required
def detail():
    row = _find(request.args.get("request_id"))
    if row is None:
        return _page("申請が見つかりません", 400)
    item = next(r for r in _rows() if r["id"] == row["id"])
    return render_template("train_tickets/detail.html", r=item)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"requests": [
        {"id": r["id"], "employee": r["employee_no"], "quantity": r["quantity"],
         "unit_price": r["unit_price"], "amount_incl_tax": r["amount_incl_tax"], "state": r["state"]}
        for r in _rows()
    ]})

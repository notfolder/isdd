"""ソフトウェアの購入の申請。画面（Blueprint）をここに置く。"""

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.software import logic

TITLE = "ソフトウェアの購入の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS software_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

bp = Blueprint("software", __name__, url_prefix="/software", template_folder="templates")


def _render_index(error=None, status=200):
    state = request.args.get("state") or None
    conn = get_db()
    employees = conn.execute("SELECT employee_no, name FROM employees WHERE status != 'retired' ORDER BY employee_no").fetchall()
    return (
        render_template(
            "software/index.html",
            requests=logic.list_requests(conn, state),
            employees=employees,
            states=logic.STATE_LABELS,
            state=state,
            error=error,
        ),
        status,
    )


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    conn = get_db()
    try:
        new_id = logic.apply(conn, request.form.get("employee_no"), request.form.get("quantity"), request.form.get("unit_price"))
    except logic.RequestError as e:
        return _render_index(str(e), 400)
    audit.record("software", "apply", str(new_id))
    conn.commit()
    return redirect(url_for("software.index"))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    conn = get_db()
    try:
        req = logic.approve(conn, request.form.get("request_id"), current_user()["employee_no"])
    except logic.RequestError as e:
        return _render_index(str(e), 400)
    audit.record("software", "approve", str(req.id))
    conn.commit()
    return redirect(url_for("software.index"))


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    conn = get_db()
    try:
        req = logic.reject(conn, request.form.get("request_id"))
    except logic.RequestError as e:
        return _render_index(str(e), 400)
    audit.record("software", "reject", str(req.id))
    conn.commit()
    return redirect(url_for("software.index"))


@bp.route("/detail")
@login_required
def detail():
    req = logic.get_request(get_db(), request.args.get("request_id"))
    if req is None:
        abort(404)
    return render_template("software/detail.html", req=req)


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {
            "id": r.id,
            "employee": r.employee_no,
            "quantity": r.quantity,
            "unit_price": r.unit_price,
            "amount_incl_tax": r.total,
            "state": r.state,
        }
        for r in logic.list_requests(get_db())
    ]
    return jsonify({"requests": items})

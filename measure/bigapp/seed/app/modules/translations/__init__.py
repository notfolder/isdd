"""機能「翻訳の申請」。数量と税抜き単価を記録し、承認か却下で決める。"""

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db

from . import logic

bp = Blueprint("translations", __name__, url_prefix="/translations", template_folder="templates")
TITLE = "翻訳の申請"
SCHEMA = """
CREATE TABLE IF NOT EXISTS translations_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""


def _render_index(error=None, status=200):
    state = request.values.get("state", "").strip()
    if state not in logic.STATES:
        state = ""
    employees = get_db().execute("SELECT employee_no, name, status FROM employees ORDER BY employee_no").fetchall()
    html = render_template(
        "translations/index.html",
        title=TITLE,
        rows=logic.list_requests(state or None),
        state=state,
        states=logic.STATES,
        employees=[e for e in employees if e["status"] not in logic.EXCLUDED_STATUSES],
        error=error,
    )
    return html, status


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    try:
        new_id = logic.apply(request.form.get("employee_no", ""), request.form.get("quantity"), request.form.get("unit_price"))
    except logic.RequestError as e:
        return _render_index(str(e), 400)
    audit.record("translations", "apply", str(new_id))
    get_db().commit()
    return redirect(url_for("translations.index"))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    try:
        target = logic.approve(request.form.get("request_id"), current_user()["employee_no"])
    except logic.RequestError as e:
        return _render_index(str(e), 400)
    audit.record("translations", "approve", str(target))
    get_db().commit()
    return redirect(url_for("translations.index"))


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    try:
        target = logic.reject(request.form.get("request_id"))
    except logic.RequestError as e:
        return _render_index(str(e), 400)
    audit.record("translations", "reject", str(target))
    get_db().commit()
    return redirect(url_for("translations.index"))


@bp.route("/detail")
@login_required
def detail():
    try:
        req = logic.get_request(logic.parse_request_id(request.args.get("request_id")))
    except logic.RequestError:
        req = None
    if req is None:
        abort(404)
    return render_template("translations/detail.html", title=TITLE, r=req)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(
        {
            "requests": [
                {
                    "id": r.id,
                    "employee": r.employee_no,
                    "quantity": r.quantity,
                    "unit_price": r.unit_price,
                    "amount_incl_tax": r.amount_incl_tax,
                    "state": r.state,
                }
                for r in logic.list_requests()
            ]
        }
    )

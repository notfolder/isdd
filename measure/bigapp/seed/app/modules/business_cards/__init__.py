"""名刺の申請。数量と税抜きの単価を記録し、税込みの金額を計算して残す。"""

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.business_cards import logic

TITLE = "名刺の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS business_cards_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

bp = Blueprint("business_cards", __name__, url_prefix="/business_cards", template_folder="templates")


def _page(error=None, status=200):
    """一覧の画面。state で絞り込める。"""
    state = request.args.get("state") or None
    if state not in logic.STATES:
        state = None
    html = render_template(
        "business_cards/index.html",
        rows=logic.list_requests(state),
        employees=logic.active_employees(),
        state=state,
        states=logic.STATES,
        error=error,
    )
    return html, status


def _act(action, func):
    """データを変える操作の共通の流れ。失敗は 400、成功は記録して一覧へ。"""
    try:
        target = func()
    except logic.RequestError as exc:
        return _page(str(exc), 400)
    audit.record("business_cards", action, str(target))
    get_db().commit()
    return redirect(url_for("business_cards.index"))


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    return _act("apply", lambda: logic.apply(form.get("employee_no"), form.get("quantity"), form.get("unit_price")))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return _act("approve", lambda: logic.approve(request.form.get("request_id"), current_user()["employee_no"]).id)


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _act("reject", lambda: logic.reject(request.form.get("request_id")).id)


@bp.route("/detail")
@login_required
def detail():
    req = logic.get_request(request.args.get("request_id"))
    if req is None:
        abort(404)
    return render_template("business_cards/detail.html", r=req)


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

"""クリーニングの申請（総務規程 第 5 条・第 6 条・第 7 条）。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.cleaning import logic

TITLE = "クリーニングの申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS cleaning_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL REFERENCES employees(employee_no),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

bp = Blueprint("cleaning", __name__, url_prefix="/cleaning", template_folder="templates")


def _page(error=None, status=200, state=None):
    """一覧の画面。エラーがあるときは理由を出して 400 などを返す。"""
    conn = get_db()
    employees = conn.execute(
        "SELECT employee_no, name FROM employees WHERE status != 'retired' ORDER BY employee_no"
    ).fetchall()
    html = render_template(
        "cleaning/index.html",
        requests=logic.list_requests(conn, state),
        employees=employees,
        states=logic.STATES,
        labels=logic.STATE_LABELS,
        selected=state,
        error=error,
    )
    return html, status


@bp.route("/")
@login_required
def index():
    state = request.args.get("state") or None
    if state is not None and state not in logic.STATES:
        return _page("状態が正しくありません", 400)
    return _page(state=state)


def _change(action, operation):
    """データを変える操作の共通の流れ。成功したら記録して一覧へ戻り、失敗したら 400 を返す。"""
    conn = get_db()
    try:
        target = operation(conn)
    except logic.RuleError as exc:
        conn.rollback()
        return _page(str(exc), 400)
    audit.record("cleaning", action, str(target))
    conn.commit()
    return redirect("/cleaning/")


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    return _change(
        "apply",
        lambda conn: logic.apply(conn, form.get("employee_no"), form.get("quantity"), form.get("unit_price")),
    )


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return _change(
        "approve",
        lambda conn: logic.approve(conn, request.form.get("request_id"), current_user()["employee_no"]),
    )


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _change("reject", lambda conn: logic.reject(conn, request.form.get("request_id")))


@bp.route("/detail")
@login_required
def detail():
    target = logic.get_request(get_db(), request.args.get("request_id"))
    if target is None:
        return render_template("cleaning/detail.html", item=None, error="申請が見つかりません"), 404
    return render_template("cleaning/detail.html", item=target, error=None)


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
                for r in logic.list_requests(get_db())
            ]
        }
    )

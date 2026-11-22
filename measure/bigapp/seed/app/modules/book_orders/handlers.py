"""書籍の購入の申請の画面。"""

from flask import abort, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.book_orders import bp, queries, rules


def _page(error=None, status=200, state=None):
    rows = queries.list_requests(state)
    return render_template("book_orders/index.html", rows=rows, error=error, state=state, labels=rules.STATE_LABELS, states=rules.STATES), status


def _fail(message):
    return _page(error=message, status=400)


def _target_request():
    """フォームの request_id から申請を探す。無ければ None。"""
    text = request.form.get("request_id", "").strip()
    if not text.isascii() or not text.isdigit():
        return None
    return queries.find_request(int(text))


@bp.route("/")
@login_required
def index():
    state = request.args.get("state", "").strip() or None
    if state is not None and state not in rules.STATES:
        return _page(error="状態が正しくありません", status=400)
    return _page(state=state)


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    employee_no = form.get("employee_no", "").strip()
    if queries.find_active_employee(employee_no) is None:
        return _fail("在籍している社員を指定してください")
    quantity = rules.parse_int(form.get("quantity"), rules.QUANTITY_MIN, rules.QUANTITY_MAX)
    if quantity is None:
        return _fail("数量は 1 以上 20 以下の整数で入力してください")
    unit_price = rules.parse_int(form.get("unit_price"), rules.UNIT_PRICE_MIN, rules.UNIT_PRICE_MAX)
    if unit_price is None:
        return _fail("単価は 1 以上 100000 以下の整数（円）で入力してください")
    amount = rules.gross_amount(quantity, unit_price)
    new_id = queries.insert_request(employee_no, quantity, unit_price, amount, clock.today().isoformat())
    audit.record("book_orders", "apply", str(new_id))
    get_db().commit()
    return redirect("/book_orders/")


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    row = _target_request()
    if row is None:
        return _fail("申請が見つかりません")
    if not rules.can_decide(row["state"]):
        return _fail("申請中の申請だけ承認できます")
    if not rules.can_approve(row["state"], row["employee_no"], current_user()["employee_no"]):
        return _fail("自分の申請は承認できません")
    queries.update_state(row["id"], "approved")
    audit.record("book_orders", "approve", str(row["id"]))
    get_db().commit()
    return redirect("/book_orders/")


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    row = _target_request()
    if row is None:
        return _fail("申請が見つかりません")
    if not rules.can_decide(row["state"]):
        return _fail("申請中の申請だけ却下できます")
    queries.update_state(row["id"], "rejected")
    audit.record("book_orders", "reject", str(row["id"]))
    get_db().commit()
    return redirect("/book_orders/")


@bp.route("/detail")
@login_required
def detail():
    text = request.args.get("request_id", "").strip()
    row = queries.find_request(int(text)) if text.isascii() and text.isdigit() else None
    if row is None:
        abort(404)
    net = row["quantity"] * row["unit_price"]
    return render_template("book_orders/detail.html", r=row, net=net, labels=rules.STATE_LABELS)


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
                for r in queries.list_requests()
            ]
        }
    )

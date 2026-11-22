"""制服の購入の申請。数量と税抜きの単価を記録し、税込みの金額を計算して、承認か却下で終える。"""

from flask import Blueprint, abort, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db

TITLE = "制服の購入の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS uniform_orders_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

bp = Blueprint("uniform_orders", __name__, url_prefix="/uniform_orders", template_folder="templates")

STATES = ("pending", "approved", "rejected")
MAX_QUANTITY = 20
MAX_UNIT_PRICE = 100000


def total(quantity, unit_price):
    """税込みの金額。税額を先に出して足す（1 円未満は切り捨て）。"""
    subtotal = quantity * unit_price
    tax = subtotal * 10 // 100
    return subtotal + tax


def _to_int(text):
    """半角数字だけの文字列を整数にする。それ以外は None。"""
    text = (text or "").strip()
    if text.isascii() and text.isdigit():
        return int(text)
    return None


def _rows(state=None):
    sql = (
        "SELECT r.id, r.employee_no, e.name AS employee_name, r.quantity, r.unit_price, r.state "
        "FROM uniform_orders_request r LEFT JOIN employees e ON e.employee_no = r.employee_no"
    )
    args = ()
    if state:
        sql += " WHERE r.state = ?"
        args = (state,)
    rows = get_db().execute(sql + " ORDER BY r.id", args).fetchall()
    return [dict(r, subtotal=r["quantity"] * r["unit_price"], amount_incl_tax=total(r["quantity"], r["unit_price"])) for r in rows]


def _fail(message, state=None):
    """受け付けないとき。データは変えず、400 で一覧の画面に理由を出す。"""
    return render_template("uniform_orders/index.html", rows=_rows(state), error=message, state=state or ""), 400


def _find_request(request_id):
    number = _to_int(request_id)
    if number is None:
        return None
    return get_db().execute("SELECT * FROM uniform_orders_request WHERE id = ?", (number,)).fetchone()


@bp.route("/")
@login_required
def index():
    state = request.args.get("state", "").strip()
    if state and state not in STATES:
        return _fail("状態が正しくありません", None)
    return render_template("uniform_orders/index.html", rows=_rows(state or None), error=None, state=state)


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    number = form.get("employee_no", "").strip()
    quantity = _to_int(form.get("quantity"))
    unit_price = _to_int(form.get("unit_price"))
    employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
    if employee is None:
        return _fail("社員が見つかりません")
    if employee["status"] == "retired":
        return _fail("退職した社員は申請できません")
    if quantity is None or not 1 <= quantity <= MAX_QUANTITY:
        return _fail(f"数量は 1 以上 {MAX_QUANTITY} 以下の整数で入力してください")
    if unit_price is None or not 1 <= unit_price <= MAX_UNIT_PRICE:
        return _fail(f"単価は 1 以上 {MAX_UNIT_PRICE} 以下の整数で入力してください")
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO uniform_orders_request (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, 'pending')",
        (number, quantity, unit_price),
    )
    audit.record("uniform_orders", "apply", str(cursor.lastrowid))
    conn.commit()
    return redirect("/uniform_orders/")


def _decide(action, new_state):
    """承認と却下の共通の処理。申請中のものだけを決める。"""
    row = _find_request(request.form.get("request_id"))
    if row is None:
        return _fail("申請が見つかりません")
    if row["state"] != "pending":
        return _fail("申請中の申請だけが対象です")
    if action == "approve" and row["employee_no"] == current_user()["employee_no"]:
        return _fail("自分の申請は承認できません")
    conn = get_db()
    conn.execute("UPDATE uniform_orders_request SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("uniform_orders", action, str(row["id"]))
    conn.commit()
    return redirect("/uniform_orders/")


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
    row = _find_request(request.args.get("request_id"))
    if row is None:
        abort(404)
    item = next(r for r in _rows() if r["id"] == row["id"])
    return render_template("uniform_orders/detail.html", item=item)


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
                for r in _rows()
            ]
        }
    )

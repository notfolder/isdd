"""切手の申請。数量と税抜きの単価を記録し、税込みの金額を計算して残す（総務規程 第 5 条）。"""

import re
from decimal import ROUND_DOWN, Decimal

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db

bp = Blueprint("stamps", __name__, url_prefix="/stamps", template_folder="templates")
TITLE = "切手の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stamps_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
);
"""

STATES = ("pending", "approved", "rejected")
STATE_LABELS = {"pending": "申請中", "approved": "承認", "rejected": "却下"}
QUANTITY_RANGE = (1, 200)
UNIT_PRICE_RANGE = (1, 100000)
TAX_RATE = Decimal("1.10")


def gross_amount(quantity, unit_price):
    """税込みの金額。数量 × 単価に消費税 10% を足し、1 円未満を切り捨てる。"""
    net = Decimal(quantity) * Decimal(unit_price)
    return int((net * TAX_RATE).quantize(Decimal("1"), rounding=ROUND_DOWN))


def is_retired(employee):
    """退職した社員か。"""
    return employee["status"] == "retired"


def parse_int(text, low, high):
    """半角数字だけの整数を low 以上 high 以下で読む。正しくなければ None。"""
    text = (text or "").strip()
    if not re.fullmatch(r"[0-9]+", text):
        return None
    value = int(text)
    return value if low <= value <= high else None


def _requests(state=None):
    sql = "SELECT r.*, e.name AS employee_name FROM stamps_requests r LEFT JOIN employees e ON e.employee_no = r.employee_no"
    args = ()
    if state:
        sql += " WHERE r.state = ?"
        args = (state,)
    return get_db().execute(sql + " ORDER BY r.id", args).fetchall()


def _page(error=None, status=200):
    """一覧の画面。state で絞り込める。"""
    state = request.values.get("state") or None
    if state not in STATES:
        state = None
    html = render_template("stamps/index.html", rows=_requests(state), state=state, states=STATES, labels=STATE_LABELS, error=error)
    return html, status


def _fail(message):
    return _page(error=message, status=400)


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    number = request.form.get("employee_no", "").strip()
    employee = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
    if employee is None:
        return _fail("社員が見つかりません")
    in_service = not is_retired(employee)
    if not in_service:
        return _fail("退職した社員は申請できません")
    quantity = parse_int(request.form.get("quantity"), *QUANTITY_RANGE)
    if quantity is None:
        return _fail("数量は 1 以上 200 以下の整数で入力してください")
    unit_price = parse_int(request.form.get("unit_price"), *UNIT_PRICE_RANGE)
    if unit_price is None:
        return _fail("単価は 1 以上 100000 以下の整数で入力してください")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO stamps_requests (employee_no, quantity, unit_price, amount_incl_tax, state) VALUES (?, ?, ?, ?, 'pending')",
        (number, quantity, unit_price, gross_amount(quantity, unit_price)),
    )
    audit.record("stamps", "apply", str(cur.lastrowid))
    conn.commit()
    return redirect(url_for("stamps.index"))


def _pending_request():
    """request_id の申請。見つからない、または申請中でなければ (None, 理由)。"""
    rid = parse_int(request.form.get("request_id"), 1, 2**62)
    row = get_db().execute("SELECT * FROM stamps_requests WHERE id = ?", (rid,)).fetchone() if rid else None
    if row is None:
        return None, "申請が見つかりません"
    if row["state"] != "pending":
        return None, "申請中の申請だけ承認・却下できます"
    return row, None


def _decide(action, new_state):
    row, error = _pending_request()
    if error:
        return _fail(error)
    if action == "approve" and row["employee_no"] == current_user()["employee_no"]:
        return _fail("自分の申請は承認できません")
    conn = get_db()
    conn.execute("UPDATE stamps_requests SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("stamps", action, str(row["id"]))
    conn.commit()
    return redirect(url_for("stamps.index"))


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
    rid = parse_int(request.args.get("request_id"), 1, 2**62)
    row = None
    if rid:
        row = (
            get_db()
            .execute(
                "SELECT r.*, e.name AS employee_name FROM stamps_requests r LEFT JOIN employees e ON e.employee_no = r.employee_no WHERE r.id = ?",
                (rid,),
            )
            .fetchone()
        )
    if row is None:
        abort(404)
    net = row["quantity"] * row["unit_price"]
    return render_template("stamps/detail.html", r=row, net=net, labels=STATE_LABELS)


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
                for r in _requests()
            ]
        }
    )

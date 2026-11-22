"""贈答品の申請（総務規程 第 5 条・第 6 条・第 7 条）。"""

import re

from flask import Blueprint, abort, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db

bp = Blueprint("gifts", __name__, url_prefix="/gifts", template_folder="templates")
TITLE = "贈答品の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS gifts_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    applied_on TEXT NOT NULL
);
"""

STATES = ("pending", "approved", "rejected")
STATE_LABELS = {"pending": "申請中", "approved": "承認", "rejected": "却下"}
MAX_QUANTITY = 30
MAX_UNIT_PRICE = 100000


def parse_int(text):
    """半角数字だけの文字列を整数にする。それ以外は None。"""
    text = (text or "").strip()
    return int(text) if re.fullmatch(r"[0-9]{1,9}", text) else None


def fetch_requests(state=None):
    """申請を id の昇順で返す。state があればその状態だけ。"""
    sql = "SELECT * FROM gifts_requests"
    args = ()
    if state:
        sql += " WHERE state = ?"
        args = (state,)
    return get_db().execute(sql + " ORDER BY id", args).fetchall()


def fetch_request(request_id):
    """申請 1 件。request_id が不正または無いときは None。"""
    number = parse_int(request_id)
    if number is None:
        return None
    return get_db().execute("SELECT * FROM gifts_requests WHERE id = ?", (number,)).fetchone()


def render_index(error=None, status=200, state=None):
    """一覧の画面。エラーがあれば理由を出す。"""
    return (
        render_template("gifts/index.html", rows=fetch_requests(state), state=state, states=STATES, labels=STATE_LABELS, error=error),
        status,
    )


@bp.route("/")
@login_required
def index():
    state = request.args.get("state") or None
    if state is not None and state not in STATES:
        return render_index("状態が正しくありません", 400)
    return render_index(state=state)


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    number = request.form.get("employee_no", "").strip()
    quantity = parse_int(request.form.get("quantity"))
    unit_price = parse_int(request.form.get("unit_price"))
    conn = get_db()
    exists = conn.execute("SELECT 1 FROM employees WHERE employee_no = ?", (number,)).fetchone()
    in_service = conn.execute("SELECT 1 FROM employees WHERE employee_no = ? AND status != 'retired'", (number,)).fetchone()
    if exists is None:
        return render_index("社員が見つかりません", 400)
    if in_service is None:
        return render_index("退職した社員は申請できません", 400)
    if quantity is None or not 1 <= quantity <= MAX_QUANTITY:
        return render_index(f"数量は 1 以上 {MAX_QUANTITY} 以下の整数で入力してください", 400)
    if unit_price is None or not 1 <= unit_price <= MAX_UNIT_PRICE:
        return render_index(f"単価は 1 以上 {MAX_UNIT_PRICE} 以下の整数で入力してください", 400)
    cursor = conn.execute(
        "INSERT INTO gifts_requests (employee_no, quantity, unit_price, amount_incl_tax, state, applied_on) "
        "VALUES (?, ?, ?, CAST(? * ? * 110 / 100 AS INTEGER), 'pending', ?)",
        (number, quantity, unit_price, quantity, unit_price, clock.today().isoformat()),
    )
    audit.record("gifts", "apply", str(cursor.lastrowid))
    conn.commit()
    return redirect("/gifts/")


def decide(action, new_state):
    """承認と却下の共通の流れ。申請中のものだけを new_state にする。"""
    row = fetch_request(request.form.get("request_id"))
    if row is None:
        return render_index("申請が見つかりません", 400)
    if row["state"] != "pending":
        return render_index("申請中の申請だけが対象です", 400)
    if action == "approve" and row["employee_no"] == current_user()["employee_no"]:
        return render_index("自分の申請は承認できません", 400)
    conn = get_db()
    conn.execute("UPDATE gifts_requests SET state = ? WHERE id = ?", (new_state, row["id"]))
    audit.record("gifts", action, str(row["id"]))
    conn.commit()
    return redirect("/gifts/")


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return decide("approve", "approved")


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return decide("reject", "rejected")


@bp.route("/detail")
@login_required
def detail():
    row = fetch_request(request.args.get("request_id"))
    if row is None:
        abort(404)
    employee = get_db().execute("SELECT name FROM employees WHERE employee_no = ?", (row["employee_no"],)).fetchone()
    amount_excl_tax = row["quantity"] * row["unit_price"]
    return render_template("gifts/detail.html", r=row, employee=employee, amount_excl_tax=amount_excl_tax, labels=STATE_LABELS)


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
                for r in fetch_requests()
            ]
        }
    )

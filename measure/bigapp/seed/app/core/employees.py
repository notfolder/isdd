"""社員の台帳。状態は active（在籍）と retired（退職）。"""

from flask import Blueprint, jsonify, render_template, request
from werkzeug.security import generate_password_hash

from app.core import audit
from app.core.auth import staff_required
from app.core.db import get_db

bp = Blueprint("employees", __name__)
ROLES = ("staff", "employee")


def _all():
    return get_db().execute("SELECT employee_no, name, dept, role, status FROM employees ORDER BY employee_no").fetchall()


@bp.route("/employees/")
@staff_required
def index():
    return render_template("employees.html", rows=_all(), error=None)


@bp.route("/employees.json")
@staff_required
def index_json():
    return jsonify({"employees": [dict(r) for r in _all()]})


@bp.route("/employees/new", methods=["POST"])
@staff_required
def create():
    form = request.form
    number, name, role = form.get("employee_no", "").strip(), form.get("name", "").strip(), form.get("role", "employee")
    error = None
    if not (number.isdigit() and len(number) == 6):
        error = "社員番号は 6 桁の数字で入力してください"
    elif not name:
        error = "名前を入力してください"
    elif role not in ROLES:
        error = "役割が正しくありません"
    elif get_db().execute("SELECT 1 FROM employees WHERE employee_no = ?", (number,)).fetchone():
        error = "この社員番号は既に登録されています"
    if error:
        return render_template("employees.html", rows=_all(), error=error), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO employees (employee_no, name, dept, role, status, password_hash) VALUES (?, ?, ?, ?, 'active', ?)",
        (number, name, form.get("dept", "").strip(), role, generate_password_hash(form.get("password") or "password1")),
    )
    audit.record("employees", "create", number)
    conn.commit()
    return render_template("employees.html", rows=_all(), error=None), 201


@bp.route("/employees/retire", methods=["POST"])
@staff_required
def retire():
    number = request.form.get("employee_no", "")
    conn = get_db()
    if conn.execute("SELECT 1 FROM employees WHERE employee_no = ?", (number,)).fetchone() is None:
        return render_template("employees.html", rows=_all(), error="社員が見つかりません"), 400
    conn.execute("UPDATE employees SET status = 'retired' WHERE employee_no = ?", (number,))
    audit.record("employees", "retire", number)
    conn.commit()
    return render_template("employees.html", rows=_all(), error=None)

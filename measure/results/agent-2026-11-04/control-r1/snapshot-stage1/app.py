import os
import re
import secrets
import sqlite3
import time
from datetime import datetime

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")
SECRET_KEY_PATH = os.path.join(DATA_DIR, "secret_key")

MANAGER = "担当者"
MEMBER = "社員"

MSG_MANAGER_ONLY = "この操作は担当者だけが行えます"
MSG_LOGIN_FAILED = "社員番号またはパスワードが違います"
MSG_REGISTERED = "登録しました。ログインしてください"
MSG_TIMEOUT = "一定時間操作がなかったため、自動でログアウトしました"
MSG_EMP_FORMAT = "社員番号は 6 桁の数字で入力してください"
MSG_EMP_DUP = "この社員番号は既に登録されています"
MSG_NAME_EMPTY = "名前を入力してください"
MSG_NAME_LONG = "名前は 30 文字以内で入力してください"
MSG_PASSWORD_SHORT = "パスワードは 8 文字以上で入力してください"
MSG_EQ_FORMAT = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
MSG_EQ_DUP = "この管理番号は既に使われています"
MSG_EQ_NAME_EMPTY = "備品名を入力してください"
MSG_EQ_NAME_LONG = "備品名は 50 文字以内で入力してください"


def idle_timeout():
    try:
        return int(os.environ.get("SESSION_IDLE_TIMEOUT_SECONDS", "1800"))
    except ValueError:
        return 1800


def load_secret_key():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SECRET_KEY_PATH):
        with open(SECRET_KEY_PATH, "w", encoding="utf-8") as f:
            f.write(secrets.token_hex(32))
    with open(SECRET_KEY_PATH, encoding="utf-8") as f:
        return f.read().strip()


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            employee_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY,
            equipment_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


app = Flask(__name__)
app.secret_key = load_secret_key()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
init_db()


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=10)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.before_request
def load_user():
    g.user = None
    if "employee_id" not in session:
        return
    now = time.time()
    if now - session.get("last_seen", 0) > idle_timeout():
        session.clear()
        flash(MSG_TIMEOUT)
        return
    session["last_seen"] = now
    g.user = get_db().execute(
        "SELECT * FROM employees WHERE id = ?", (session["employee_id"],)
    ).fetchone()
    if g.user is None:
        session.clear()


@app.context_processor
def inject_user():
    user = getattr(g, "user", None)
    return {"user": user, "is_manager": bool(user) and user["role"] == MANAGER}


def manager_denied():
    """担当者でなければ応答を返す。担当者なら None。"""
    if g.user is None:
        flash(MSG_MANAGER_ONLY)
        return redirect(url_for("login"))
    if g.user["role"] != MANAGER:
        flash(MSG_MANAGER_ONLY)
        return redirect(url_for("index"))
    return None


@app.route("/")
def index():
    rows = get_db().execute(
        "SELECT id, equipment_number, name FROM equipment ORDER BY equipment_number"
    ).fetchall()
    return render_template("index.html", equipment=rows)


@app.route("/accounts/register/", methods=["GET", "POST"])
def register():
    values = {"employee_number": "", "name": ""}
    errors = {}
    if request.method == "POST":
        raw_number = request.form.get("employee_number", "")
        raw_name = request.form.get("name", "")
        password = request.form.get("password", "")
        values = {"employee_number": raw_number, "name": raw_name}
        number = raw_number.strip()
        name = raw_name.strip()

        if not re.fullmatch(r"[0-9]{6}", number):
            errors["employee_number"] = MSG_EMP_FORMAT
        if not name:
            errors["name"] = MSG_NAME_EMPTY
        elif len(name) > 30:
            errors["name"] = MSG_NAME_LONG
        if len(password) < 8:
            errors["password"] = MSG_PASSWORD_SHORT

        if not errors:
            db = get_db()
            db.execute("BEGIN IMMEDIATE")
            try:
                count = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
                role = MANAGER if count == 0 else MEMBER
                db.execute(
                    "INSERT INTO employees (employee_number, name, password_hash, role, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (number, name, generate_password_hash(password), role,
                     datetime.now().isoformat(timespec="seconds")),
                )
                db.execute("COMMIT")
            except sqlite3.IntegrityError:
                db.execute("ROLLBACK")
                errors["employee_number"] = MSG_EMP_DUP
            except Exception:
                db.execute("ROLLBACK")
                raise
            else:
                flash(MSG_REGISTERED)
                return redirect(url_for("login"))
    return render_template("register.html", values=values, errors=errors)


@app.route("/login/", methods=["GET", "POST"])
def login():
    error = None
    employee_number = ""
    if request.method == "POST":
        employee_number = request.form.get("employee_number", "")
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT * FROM employees WHERE employee_number = ?", (employee_number.strip(),)
        ).fetchone()
        if row is not None and check_password_hash(row["password_hash"], password):
            session.clear()
            session["employee_id"] = row["id"]
            session["last_seen"] = time.time()
            return redirect(url_for("index"))
        error = MSG_LOGIN_FAILED
    return render_template("login.html", error=error, employee_number=employee_number)


@app.post("/logout/")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/equipment/new/", methods=["GET", "POST"])
def equipment_new():
    denied = manager_denied()
    if denied:
        return denied
    values = {"equipment_number": "", "name": ""}
    errors = {}
    if request.method == "POST":
        raw_number = request.form.get("equipment_number", "")
        raw_name = request.form.get("name", "")
        values = {"equipment_number": raw_number, "name": raw_name}
        errors = validate_equipment(raw_number.strip(), raw_name.strip())
        if not errors:
            now = datetime.now().isoformat(timespec="seconds")
            try:
                get_db().execute(
                    "INSERT INTO equipment (equipment_number, name, created_at, updated_at)"
                    " VALUES (?, ?, ?, ?)",
                    (raw_number.strip(), raw_name.strip(), now, now),
                )
            except sqlite3.IntegrityError:
                errors["equipment_number"] = MSG_EQ_DUP
            else:
                flash("備品を登録しました")
                return redirect(url_for("index"))
    return render_template(
        "equipment_form.html",
        heading="備品の登録",
        action=url_for("equipment_new"),
        values=values,
        errors=errors,
    )


@app.route("/equipment/<int:equipment_id>/edit/", methods=["GET", "POST"])
def equipment_edit(equipment_id):
    denied = manager_denied()
    if denied:
        return denied
    db = get_db()
    row = db.execute("SELECT * FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
    if row is None:
        abort(404)
    values = {"equipment_number": row["equipment_number"], "name": row["name"]}
    errors = {}
    if request.method == "POST":
        raw_number = request.form.get("equipment_number", "")
        raw_name = request.form.get("name", "")
        values = {"equipment_number": raw_number, "name": raw_name}
        errors = validate_equipment(raw_number.strip(), raw_name.strip())
        if not errors:
            try:
                db.execute(
                    "UPDATE equipment SET equipment_number = ?, name = ?, updated_at = ? WHERE id = ?",
                    (raw_number.strip(), raw_name.strip(),
                     datetime.now().isoformat(timespec="seconds"), equipment_id),
                )
            except sqlite3.IntegrityError:
                errors["equipment_number"] = MSG_EQ_DUP
            else:
                flash("備品を修正しました")
                return redirect(url_for("index"))
    return render_template(
        "equipment_form.html",
        heading="備品の修正",
        action=url_for("equipment_edit", equipment_id=equipment_id),
        values=values,
        errors=errors,
    )


@app.post("/equipment/<int:equipment_id>/delete/")
def equipment_delete(equipment_id):
    denied = manager_denied()
    if denied:
        return denied
    get_db().execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
    flash("備品を削除しました")
    return redirect(url_for("index"))


def validate_equipment(number, name):
    errors = {}
    if not re.fullmatch(r"[A-Za-z0-9-]{1,20}", number):
        errors["equipment_number"] = MSG_EQ_FORMAT
    if not name:
        errors["name"] = MSG_EQ_NAME_EMPTY
    elif len(name) > 50:
        errors["name"] = MSG_EQ_NAME_LONG
    return errors


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))

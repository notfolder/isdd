import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")
SECRET_KEY_PATH = os.path.join(DATA_DIR, "secret_key")
JST = timezone(timedelta(hours=9))

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
MSG_EQ_STALE = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
MSG_EQ_LENT_DELETE = "この備品は貸出中のため削除できません。先に返却を処理してください"
MSG_EQ_GONE = "この備品は既に削除されています"
MSG_LEND_BORROWER = "借りる社員を選んでください"
MSG_LEND_FUTURE = "貸出日に未来の日付は入力できません"
MSG_LEND_DATE_FORMAT = "貸出日は YYYY-MM-DD の形式で入力してください"
MSG_ALREADY_LENT = "この備品は既に貸出中です"
MSG_ALREADY_RETURNED = "この備品は既に返却されています"
MSG_ACCOUNT_BORROWING = "この社員は備品を借りているため削除できません。先に返却を処理してください"
MSG_LAST_MANAGER = "担当者が 1 人もいなくなるため、この操作はできません"
MSG_ACCOUNT_GONE = "この社員は既に削除されています"
MSG_ROLE_TO_MANAGER = "担当者にしました"
MSG_ROLE_TO_MEMBER = "担当者から外しました"
MSG_PASSWORD_RESET = "パスワードを再設定しました"
MSG_ACCOUNT_DELETED = "アカウントを削除しました"


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


def today_jst():
    return datetime.now(JST).date()


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
            updated_at TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY,
            equipment_id INTEGER NOT NULL UNIQUE REFERENCES equipment(id),
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            lent_on TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    # 段 1 で作られた DB には version 列が無いので足す。
    columns = {row[1] for row in conn.execute("PRAGMA table_info(equipment)")}
    if "version" not in columns:
        conn.execute("ALTER TABLE equipment ADD COLUMN version INTEGER NOT NULL DEFAULT 0")
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
        "SELECT e.id, e.equipment_number, e.name, e.version,"
        " l.lent_on, m.name AS borrower_name"
        " FROM equipment e"
        " LEFT JOIN loans l ON l.equipment_id = e.id"
        " LEFT JOIN employees m ON m.id = l.employee_id"
        " ORDER BY e.equipment_number"
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
        error=None,
        version=None,
    )


@app.route("/equipment/<int:equipment_id>/edit/", methods=["GET", "POST"])
def equipment_edit(equipment_id):
    denied = manager_denied()
    if denied:
        return denied
    db = get_db()
    error = None
    if request.method == "GET":
        row = db.execute("SELECT * FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
        if row is None:
            abort(404)
        values = {"equipment_number": row["equipment_number"], "name": row["name"]}
        version = row["version"]
        errors = {}
    else:
        raw_number = request.form.get("equipment_number", "")
        raw_name = request.form.get("name", "")
        values = {"equipment_number": raw_number, "name": raw_name}
        version = request.form.get("version", "")
        errors = validate_equipment(raw_number.strip(), raw_name.strip())
        if not errors:
            # 開いた時点の version と一致するときだけ保存する（他の担当者の修正・削除を検出する）。
            db.execute("BEGIN IMMEDIATE")
            try:
                cur = db.execute(
                    "UPDATE equipment SET equipment_number = ?, name = ?, updated_at = ?,"
                    " version = version + 1 WHERE id = ? AND version = ?",
                    (raw_number.strip(), raw_name.strip(),
                     datetime.now().isoformat(timespec="seconds"), equipment_id,
                     int(version) if version.isdigit() else -1),
                )
                if cur.rowcount == 0:
                    db.execute("ROLLBACK")
                    error = MSG_EQ_STALE
                else:
                    db.execute("COMMIT")
                    flash("備品を修正しました")
                    return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                db.execute("ROLLBACK")
                errors["equipment_number"] = MSG_EQ_DUP
            except Exception:
                db.execute("ROLLBACK")
                raise
    return render_template(
        "equipment_form.html",
        heading="備品の修正",
        action=url_for("equipment_edit", equipment_id=equipment_id),
        values=values,
        errors=errors,
        error=error,
        version=version,
    )


@app.post("/equipment/<int:equipment_id>/delete/")
def equipment_delete(equipment_id):
    denied = manager_denied()
    if denied:
        return denied
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        exists = db.execute("SELECT 1 FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
        if exists is None:
            db.execute("COMMIT")
            flash(MSG_EQ_GONE)
        elif db.execute("SELECT 1 FROM loans WHERE equipment_id = ?", (equipment_id,)).fetchone():
            db.execute("COMMIT")
            flash(MSG_EQ_LENT_DELETE)
        else:
            db.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
            db.execute("COMMIT")
            flash("備品を削除しました")
    except Exception:
        db.execute("ROLLBACK")
        raise
    return redirect(url_for("index"))


@app.route("/equipment/<int:equipment_id>/lend/", methods=["GET", "POST"])
def equipment_lend(equipment_id):
    denied = manager_denied()
    if denied:
        return denied
    db = get_db()
    equipment = db.execute(
        "SELECT id, equipment_number, name FROM equipment WHERE id = ?", (equipment_id,)
    ).fetchone()
    if equipment is None:
        abort(404)
    if db.execute("SELECT 1 FROM loans WHERE equipment_id = ?", (equipment_id,)).fetchone():
        flash(MSG_ALREADY_LENT)
        return redirect(url_for("index"))

    employees = db.execute(
        "SELECT id, employee_number, name FROM employees ORDER BY employee_number"
    ).fetchall()
    values = {"borrower": "", "lent_on": today_jst().isoformat()}
    errors = {}
    if request.method == "POST":
        borrower = request.form.get("borrower", "").strip()
        lent_on_raw = request.form.get("lent_on", "").strip()
        values = {"borrower": borrower, "lent_on": lent_on_raw}
        employee_ids = {str(row["id"]) for row in employees}
        if borrower not in employee_ids:
            errors["borrower"] = MSG_LEND_BORROWER
        lent_on = None
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", lent_on_raw):
            errors["lent_on"] = MSG_LEND_DATE_FORMAT
        else:
            try:
                lent_on = datetime.strptime(lent_on_raw, "%Y-%m-%d").date()
            except ValueError:
                errors["lent_on"] = MSG_LEND_DATE_FORMAT
        if lent_on is not None and lent_on > today_jst():
            errors["lent_on"] = MSG_LEND_FUTURE

        if not errors:
            db.execute("BEGIN IMMEDIATE")
            try:
                still = db.execute("SELECT 1 FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
                if still is None:
                    db.execute("COMMIT")
                    flash(MSG_EQ_GONE)
                    return redirect(url_for("index"))
                if db.execute("SELECT 1 FROM loans WHERE equipment_id = ?", (equipment_id,)).fetchone():
                    db.execute("COMMIT")
                    flash(MSG_ALREADY_LENT)
                    return redirect(url_for("index"))
                db.execute(
                    "INSERT INTO loans (equipment_id, employee_id, lent_on, created_at)"
                    " VALUES (?, ?, ?, ?)",
                    (equipment_id, int(borrower), lent_on.isoformat(),
                     datetime.now().isoformat(timespec="seconds")),
                )
                db.execute("COMMIT")
            except sqlite3.IntegrityError:
                db.execute("ROLLBACK")
                flash(MSG_ALREADY_LENT)
                return redirect(url_for("index"))
            except Exception:
                db.execute("ROLLBACK")
                raise
            flash("貸出を登録しました")
            return redirect(url_for("index"))

    return render_template(
        "lend.html",
        equipment=equipment,
        employees=employees,
        values=values,
        errors=errors,
        action=url_for("equipment_lend", equipment_id=equipment_id),
    )


@app.post("/equipment/<int:equipment_id>/return/")
def equipment_return(equipment_id):
    denied = manager_denied()
    if denied:
        return denied
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        loan = db.execute("SELECT id FROM loans WHERE equipment_id = ?", (equipment_id,)).fetchone()
        if loan is None:
            db.execute("COMMIT")
            flash(MSG_ALREADY_RETURNED)
        else:
            # 返却した貸出の記録は残さない。
            db.execute("DELETE FROM loans WHERE id = ?", (loan["id"],))
            db.execute("COMMIT")
            flash("返却を処理しました")
    except Exception:
        db.execute("ROLLBACK")
        raise
    return redirect(url_for("index"))


def count_managers(db):
    return db.execute("SELECT COUNT(*) FROM employees WHERE role = ?", (MANAGER,)).fetchone()[0]


def render_accounts(reset_id=None, reset_value="", reset_error=None):
    employees = get_db().execute(
        "SELECT id, employee_number, name, role FROM employees ORDER BY employee_number"
    ).fetchall()
    return render_template(
        "accounts.html",
        employees=employees,
        reset_id=reset_id,
        reset_value=reset_value,
        reset_error=reset_error,
    )


@app.get("/accounts/")
def accounts():
    denied = manager_denied()
    if denied:
        return denied
    return render_accounts(reset_id=request.args.get("reset", type=int))


@app.post("/accounts/<int:employee_id>/role/")
def account_role(employee_id):
    denied = manager_denied()
    if denied:
        return denied
    to = request.form.get("to", "")
    if to not in (MANAGER, MEMBER):
        abort(400)
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        target = db.execute("SELECT id, role FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if target is None:
            db.execute("COMMIT")
            flash(MSG_ACCOUNT_GONE)
        elif target["role"] == to:
            db.execute("COMMIT")
        elif to == MEMBER and count_managers(db) <= 1:
            db.execute("COMMIT")
            flash(MSG_LAST_MANAGER)
        else:
            db.execute("UPDATE employees SET role = ? WHERE id = ?", (to, employee_id))
            db.execute("COMMIT")
            flash(MSG_ROLE_TO_MANAGER if to == MANAGER else MSG_ROLE_TO_MEMBER)
    except Exception:
        db.execute("ROLLBACK")
        raise
    return redirect(url_for("accounts"))


@app.post("/accounts/<int:employee_id>/password/")
def account_password(employee_id):
    denied = manager_denied()
    if denied:
        return denied
    db = get_db()
    if db.execute("SELECT 1 FROM employees WHERE id = ?", (employee_id,)).fetchone() is None:
        abort(404)
    value = request.form.get("new_password", "")
    if len(value) < 8:
        return render_accounts(reset_id=employee_id, reset_value=value,
                               reset_error=MSG_PASSWORD_SHORT)
    db.execute(
        "UPDATE employees SET password_hash = ? WHERE id = ?",
        (generate_password_hash(value), employee_id),
    )
    flash(MSG_PASSWORD_RESET)
    return redirect(url_for("accounts"))


@app.post("/accounts/<int:employee_id>/delete/")
def account_delete(employee_id):
    denied = manager_denied()
    if denied:
        return denied
    db = get_db()
    deleted = False
    db.execute("BEGIN IMMEDIATE")
    try:
        target = db.execute("SELECT id, role FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if target is None:
            db.execute("COMMIT")
            flash(MSG_ACCOUNT_GONE)
        elif db.execute("SELECT 1 FROM loans WHERE employee_id = ?", (employee_id,)).fetchone():
            db.execute("COMMIT")
            flash(MSG_ACCOUNT_BORROWING)
        elif target["role"] == MANAGER and count_managers(db) <= 1:
            db.execute("COMMIT")
            flash(MSG_LAST_MANAGER)
        else:
            db.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            db.execute("COMMIT")
            deleted = True
            flash(MSG_ACCOUNT_DELETED)
    except Exception:
        db.execute("ROLLBACK")
        raise
    if deleted and employee_id == session.get("employee_id"):
        # 自分のアカウントを削除したときは、そのままログアウトする。
        session.clear()
        flash(MSG_ACCOUNT_DELETED)
        return redirect(url_for("index"))
    return redirect(url_for("accounts"))


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

    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), threads=16)

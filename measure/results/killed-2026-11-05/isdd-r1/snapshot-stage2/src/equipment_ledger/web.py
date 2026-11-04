"""Web アプリの作成と画面（ルート）。

画面の入力は validation で検証し、業務の処理は accounts・equipment に任せる。
権限は auth.require_manager で要求ごとに判定する。
"""

import contextlib
import os
import secrets
from pathlib import Path

from flask import Blueprint, Flask, current_app, flash, redirect, render_template, request, url_for

from equipment_ledger import accounts, auth, db, equipment, lending, validation

LOGIN_FAILED_MESSAGE = "社員番号またはパスワードが違います"
SECRET_KEY_FILE = "secret_key"

ledger = Blueprint("ledger", __name__)


@ledger.route("/")
def equipment_status():
    """貸出状況の一覧。誰でも見られる。"""
    rows = equipment.list_equipment(db.get_db())
    return render_template("status.html", equipment=rows)


@ledger.route("/accounts/register/", methods=["GET", "POST"])
def register_account():
    """アカウント登録。成功したらログイン画面へ移る。"""
    form = {"employee_number": "", "name": "", "password": ""}
    errors = {}
    if request.method == "POST":
        form, errors = validation.validate_account_input(
            request.form.get("employee_number"),
            request.form.get("name"),
            request.form.get("password"),
        )
        if not errors:
            _role, error = accounts.register_account(
                db.get_db(), form["employee_number"], form["name"], form["password"]
            )
            if error is None:
                flash("登録しました。ログインしてください", "message")
                return redirect(url_for("ledger.login"))
            errors["employee_number"] = error
    return render_template("register.html", form=form, errors=errors)


@ledger.route("/login/", methods=["GET", "POST"])
def login():
    """ログイン。失敗しても、社員番号とパスワードのどちらが違うかは示さない。"""
    error = None
    employee_number = ""
    if request.method == "POST":
        employee_number = (request.form.get("employee_number") or "").strip()
        account = accounts.authenticate_account(
            db.get_db(), employee_number, request.form.get("password") or ""
        )
        if account is None:
            error = LOGIN_FAILED_MESSAGE
        else:
            auth.log_in(account["id"])
            return redirect(url_for("ledger.equipment_status"))
    return render_template("login.html", error=error, employee_number=employee_number)


@ledger.route("/logout/", methods=["POST"])
def logout():
    """ログアウトする。"""
    auth.log_out()
    return redirect(url_for("ledger.equipment_status"))


@ledger.route("/equipment/new/", methods=["GET", "POST"])
@auth.require_manager
def new_equipment():
    """備品の登録（担当者だけ）。"""
    form = {"equipment_number": "", "name": ""}
    errors = {}
    if request.method == "POST":
        form, errors = validation.validate_equipment_input(
            request.form.get("equipment_number"), request.form.get("name")
        )
        if not errors:
            error = equipment.create_equipment(db.get_db(), form["equipment_number"], form["name"])
            if error is None:
                flash("備品を登録しました", "message")
                return redirect(url_for("ledger.equipment_status"))
            errors["equipment_number"] = error
    return render_template("equipment_form.html", mode="new", form=form, errors=errors, target_number="")


@ledger.route("/equipment/<equipment_number>/edit/", methods=["GET", "POST"])
@auth.require_manager
def edit_equipment(equipment_number):
    """備品の修正（担当者だけ）。開いたときの版番号と違えば、他の担当者の更新として保存しない。"""
    if request.method == "GET":
        target = equipment.find_equipment(db.get_db(), equipment_number)
        if target is None:
            flash(equipment.NOT_FOUND_MESSAGE, "message")
            return redirect(url_for("ledger.equipment_status"))
        form = {"equipment_number": target["equipment_number"], "name": target["name"]}
        revision = target["revision"]
        errors = {}
        conflict = None
    else:
        revision = request.form.get("revision", "")
        form, errors = validation.validate_equipment_input(
            request.form.get("equipment_number"), request.form.get("name")
        )
        conflict = None
        if not errors:
            error = equipment.update_equipment(
                db.get_db(), equipment_number, revision, form["equipment_number"], form["name"]
            )
            if error is None:
                flash("備品を修正しました", "message")
                return redirect(url_for("ledger.equipment_status"))
            if error == equipment.CONFLICT_MESSAGE:
                conflict = error
            else:
                errors["equipment_number"] = error
    return render_template(
        "equipment_form.html",
        mode="edit",
        form=form,
        errors=errors,
        conflict=conflict,
        revision=revision,
        target_number=equipment_number,
    )


@ledger.route("/equipment/<equipment_number>/delete/", methods=["POST"])
@auth.require_manager
def delete_equipment(equipment_number):
    """備品の削除（担当者だけ）。確認は画面側のダイアログで行う。貸出中の備品は削除しない。"""
    error = equipment.delete_equipment(db.get_db(), equipment_number)
    flash("備品を削除しました" if error is None else error, "message")
    return redirect(url_for("ledger.equipment_status"))


@ledger.route("/equipment/<equipment_number>/lend/", methods=["GET", "POST"])
@auth.require_manager
def lend_equipment(equipment_number):
    """貸出の登録（担当者だけ）。貸出中の備品と存在しない備品は、貸出状況へ戻して知らせる。"""
    conn = db.get_db()
    target = equipment.find_equipment(conn, equipment_number)
    if target is None:
        flash(equipment.NOT_FOUND_MESSAGE, "message")
        return redirect(url_for("ledger.equipment_status"))
    if lending.is_lent(conn, equipment_number):
        flash(lending.ALREADY_LENT_MESSAGE, "message")
        return redirect(url_for("ledger.equipment_status"))
    form = {"borrower_id": None, "lent_on": validation.today_in_japan().isoformat()}
    errors = {}
    if request.method == "POST":
        form, errors = validation.validate_lending_input(
            request.form.get("borrower_id"),
            request.form.get("lent_on"),
            validation.today_in_japan(),
        )
        if not errors:
            error = lending.lend_equipment(
                conn, equipment_number, form["borrower_id"], form["lent_on"]
            )
            if error is None:
                flash("貸出を登録しました", "message")
                return redirect(url_for("ledger.equipment_status"))
            if error == lending.BORROWER_MISSING_MESSAGE:
                errors["borrower_id"] = error
            else:
                flash(error, "message")
                return redirect(url_for("ledger.equipment_status"))
    return render_template(
        "lending_form.html",
        equipment=target,
        form=form,
        errors=errors,
        borrowers=accounts.list_borrowers(conn),
    )


@ledger.route("/equipment/<equipment_number>/return/", methods=["POST"])
@auth.require_manager
def return_equipment(equipment_number):
    """返却の処理（担当者だけ）。貸出の記録は消し、記録は残さない。確認は画面側のダイアログで行う。"""
    error = lending.return_equipment(db.get_db(), equipment_number)
    flash("返却を処理しました" if error is None else error, "message")
    return redirect(url_for("ledger.equipment_status"))


def create_app(config):
    """設定から Flask アプリを作る。データ格納先と DB を用意し、画面の経路を登録する。"""
    data_dir = Path(config["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)
    with contextlib.closing(db.connect_database(data_dir)) as conn:
        db.initialize_database(conn)

    app = Flask(__name__)
    app.config.update(
        DATA_DIR=data_dir,
        IDLE_TIMEOUT_SECONDS=config["idle_timeout_seconds"],
        SECRET_KEY=_load_or_create_secret_key(data_dir),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    app.register_blueprint(ledger)
    app.teardown_appcontext(db.close_db)
    app.before_request(_check_idle_session)
    app.context_processor(_inject_current_user)
    return app


def _check_idle_session():
    """要求の前に無操作の期限を確かめる。"""
    auth.expire_idle_session(current_app.config["IDLE_TIMEOUT_SECONDS"])


def _inject_current_user():
    """テンプレートに、ログイン中のアカウントと担当者かどうかを渡す。"""
    account = auth.current_account()
    return {
        "current_user": account,
        "is_manager": account is not None and account["role"] == "manager",
    }


def _load_or_create_secret_key(data_dir):
    """セッションの署名鍵を読む。無ければ生成して、所有者だけが読める権限で保存する。"""
    path = data_dir / SECRET_KEY_FILE
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    key = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(key)
    return key

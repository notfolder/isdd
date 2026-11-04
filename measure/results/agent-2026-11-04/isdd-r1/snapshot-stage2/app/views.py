"""画面の要求を受け、業務の関数を呼び、画面を返す。"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from . import accounts, equipment, loans
from .auth import login_user, logout_user, require_manager
from .db import connect
from .validation import MSG_BORROWER_REQUIRED, validate_loan_input

web_blueprint = Blueprint("web", __name__)

MSG_ACCOUNT_REGISTERED = "登録しました。ログインしてください"
MSG_LOGIN_FAILED = "社員番号またはパスワードが違います"
MSG_EQUIPMENT_CREATED = "備品を登録しました"
MSG_EQUIPMENT_SAVED = "備品を保存しました"
MSG_EQUIPMENT_DELETED = "備品を削除しました"
MSG_EQUIPMENT_NOT_FOUND = "備品が見つかりません"
MSG_EQUIPMENT_LOANED_DELETE = "この備品は貸出中のため削除できません。先に返却を処理してください"
MSG_LOAN_REGISTERED = "貸出を登録しました"
MSG_LOAN_ALREADY = "この備品は既に貸出中です"
MSG_RETURNED = "返却しました"
MSG_ALREADY_RETURNED = "この備品は既に返却されています"

JST = timezone(timedelta(hours=9))


def _today_jst():
    """日本時間の今日の日付。"""
    return datetime.now(JST).date()


def _db():
    """要求ごとに DB 接続を開く。接続は要求の終わりに閉じる。"""
    if "conn" not in g:
        g.conn = connect(Path(current_app.config["DB_PATH"]))
    return g.conn


@web_blueprint.teardown_app_request
def _close_db(_exc):
    conn = g.pop("conn", None)
    if conn is not None:
        conn.close()


@web_blueprint.route("/")
def loan_status():
    manager = g.account is not None and g.account["role"] == "manager"
    items = loans.list_loan_status(_db())
    return render_template(
        "loan_status.html",
        items=items,
        manager=manager,
        guest_links=g.account is None,
    )


@web_blueprint.route("/accounts/register/", methods=["GET", "POST"])
def register_account():
    values = {"employee_number": "", "name": ""}
    errors = {}
    if request.method == "POST":
        values = {
            "employee_number": request.form.get("employee_number", ""),
            "name": request.form.get("name", ""),
        }
        errors = accounts.register_account(
            _db(),
            values["employee_number"],
            values["name"],
            request.form.get("password", ""),
        )
        if not errors:
            flash(MSG_ACCOUNT_REGISTERED)
            return redirect(url_for("web.login"))
    return render_template("account_register.html", values=values, errors=errors)


@web_blueprint.route("/login/", methods=["GET", "POST"])
def login():
    employee_number = ""
    error = None
    if request.method == "POST":
        employee_number = request.form.get("employee_number", "")
        password = request.form.get("password", "")
        account = None
        if employee_number and password:
            account = accounts.authenticate_account(_db(), employee_number, password)
        if account is not None:
            login_user(account)
            return redirect(url_for("web.loan_status"))
        error = MSG_LOGIN_FAILED
    return render_template("login.html", employee_number=employee_number, error=error)


@web_blueprint.route("/logout/", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("web.loan_status"))


@web_blueprint.route("/equipment/new/", methods=["GET", "POST"])
def equipment_new():
    denied = require_manager()
    if denied is not None:
        return denied
    values = {"equipment_number": "", "name": ""}
    errors = {}
    if request.method == "POST":
        values = {
            "equipment_number": request.form.get("equipment_number", ""),
            "name": request.form.get("name", ""),
        }
        errors = equipment.create_equipment(_db(), values["equipment_number"], values["name"])
        if not errors:
            flash(MSG_EQUIPMENT_CREATED)
            return redirect(url_for("web.loan_status"))
    return render_template(
        "equipment_form.html",
        values=values,
        errors=errors,
        action=url_for("web.equipment_new"),
        title="備品の登録",
    )


@web_blueprint.route("/equipment/<equipment_number>/edit/", methods=["GET", "POST"])
def equipment_edit(equipment_number: str):
    denied = require_manager()
    if denied is not None:
        return denied
    errors = {}
    if request.method == "GET":
        current = equipment.get_equipment_with_revision(_db(), equipment_number)
        if current is None:
            flash(MSG_EQUIPMENT_NOT_FOUND)
            return redirect(url_for("web.loan_status"))
        values = dict(current)
    else:
        values = {
            "equipment_number": request.form.get("equipment_number", ""),
            "name": request.form.get("name", ""),
            "revision": request.form.get("revision", ""),
        }
        expected = int(values["revision"]) if values["revision"].isdigit() else None
        errors = equipment.update_equipment_if_current(
            _db(), equipment_number, expected, values["equipment_number"], values["name"]
        )
        if not errors:
            flash(MSG_EQUIPMENT_SAVED)
            return redirect(url_for("web.loan_status"))
    return render_template(
        "equipment_form.html",
        values=values,
        errors=errors,
        action=url_for("web.equipment_edit", equipment_number=equipment_number),
        title="備品の修正",
    )


@web_blueprint.route("/equipment/<equipment_number>/delete/", methods=["POST"])
def equipment_delete(equipment_number: str):
    denied = require_manager()
    if denied is not None:
        return denied
    result = equipment.delete_equipment_if_not_loaned(_db(), equipment_number)
    if result == equipment.DELETE_DELETED:
        flash(MSG_EQUIPMENT_DELETED)
    elif result == equipment.DELETE_LOANED:
        flash(MSG_EQUIPMENT_LOANED_DELETE)
    else:
        flash(MSG_EQUIPMENT_NOT_FOUND)
    return redirect(url_for("web.loan_status"))


@web_blueprint.route("/equipment/<equipment_number>/loan/", methods=["GET", "POST"])
def equipment_loan(equipment_number: str):
    denied = require_manager()
    if denied is not None:
        return denied
    item = equipment.get_equipment_with_revision(_db(), equipment_number)
    if item is None:
        flash(MSG_EQUIPMENT_NOT_FOUND)
        return redirect(url_for("web.loan_status"))
    values = {"borrower": "", "lent_on": _today_jst().isoformat()}
    errors = {}
    if request.method == "POST":
        values = {
            "borrower": request.form.get("borrower", ""),
            "lent_on": request.form.get("lent_on", ""),
        }
        errors = validate_loan_input(values["borrower"], values["lent_on"], _today_jst())
        if not errors:
            result = loans.register_loan(
                _db(), equipment_number, int(values["borrower"]), values["lent_on"]
            )
            if result == loans.RESULT_OK:
                flash(MSG_LOAN_REGISTERED)
                return redirect(url_for("web.loan_status"))
            if result == loans.RESULT_LOANED:
                flash(MSG_LOAN_ALREADY)
                return redirect(url_for("web.loan_status"))
            if result == loans.RESULT_NOT_FOUND:
                flash(MSG_EQUIPMENT_NOT_FOUND)
                return redirect(url_for("web.loan_status"))
            errors["borrower"] = MSG_BORROWER_REQUIRED
    return render_template(
        "loan_register.html",
        item=item,
        values=values,
        errors=errors,
        borrowers=loans.list_borrowers(_db()),
        action=url_for("web.equipment_loan", equipment_number=equipment_number),
    )


@web_blueprint.route("/equipment/<equipment_number>/return/", methods=["POST"])
def equipment_return(equipment_number: str):
    denied = require_manager()
    if denied is not None:
        return denied
    result = loans.return_loan(_db(), equipment_number)
    if result == loans.RESULT_OK:
        flash(MSG_RETURNED)
    elif result == loans.RESULT_NOT_LOANED:
        flash(MSG_ALREADY_RETURNED)
    else:
        flash(MSG_EQUIPMENT_NOT_FOUND)
    return redirect(url_for("web.loan_status"))

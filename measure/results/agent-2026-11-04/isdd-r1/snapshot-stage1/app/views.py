"""画面の要求を受け、業務の関数を呼び、画面を返す。"""

from pathlib import Path

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from . import accounts, equipment
from .auth import login_user, logout_user, require_manager
from .db import connect

web_blueprint = Blueprint("web", __name__)

MSG_ACCOUNT_REGISTERED = "登録しました。ログインしてください"
MSG_LOGIN_FAILED = "社員番号またはパスワードが違います"
MSG_EQUIPMENT_CREATED = "備品を登録しました"
MSG_EQUIPMENT_SAVED = "備品を保存しました"
MSG_EQUIPMENT_DELETED = "備品を削除しました"
MSG_EQUIPMENT_NOT_FOUND = "備品が見つかりません"


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
    items = equipment.list_equipment(_db())
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
    current = equipment.get_equipment(_db(), equipment_number)
    if current is None:
        flash(MSG_EQUIPMENT_NOT_FOUND)
        return redirect(url_for("web.loan_status"))
    values = dict(current)
    errors = {}
    if request.method == "POST":
        values = {
            "equipment_number": request.form.get("equipment_number", ""),
            "name": request.form.get("name", ""),
        }
        errors = equipment.update_equipment(
            _db(), equipment_number, values["equipment_number"], values["name"]
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
    if equipment.delete_equipment(_db(), equipment_number):
        flash(MSG_EQUIPMENT_DELETED)
    else:
        flash(MSG_EQUIPMENT_NOT_FOUND)
    return redirect(url_for("web.loan_status"))

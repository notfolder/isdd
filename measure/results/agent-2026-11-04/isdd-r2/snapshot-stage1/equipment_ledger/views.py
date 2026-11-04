"""5 画面と 2 つの操作の HTTP の受け口。"""

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from .auth import current_user, log_in_user, log_out_user, require_manager
from .core.accounts import ROLE_MANAGER, authenticate, register_account
from .core.db import open_connection
from .core.equipment import (
    delete_equipment,
    get_equipment,
    list_equipment_status,
    register_equipment,
    update_equipment,
)
from .core.validation import validate_account_input, validate_equipment_input

bp = Blueprint("ledger", __name__)

MSG_LOGIN_FAILED = "社員番号またはパスワードが違います"
MSG_EMPLOYEE_NUMBER_DUPLICATE = "この社員番号は既に登録されています"
MSG_EQUIPMENT_NUMBER_DUPLICATE = "この管理番号は既に使われています"
MSG_REGISTERED = "登録しました。ログインしてください"


def _get_db():
    """要求ごとの DB 接続を返す。"""
    if "db" not in g:
        g.db = open_connection(current_app.config["DATA_DIR"])
    return g.db


@bp.get("/")
def status():
    """貸出状況の画面（誰でも見られる）。"""
    rows = list_equipment_status(_get_db())
    return render_template(
        "equipment_status.html",
        rows=rows,
        user=current_user(),
        is_manager=(current_user() or {}).get("role") == ROLE_MANAGER,
    )


@bp.route("/accounts/register/", methods=["GET", "POST"])
def register():
    """社員が自分でアカウントを登録する。"""
    values = {"employee_number": "", "name": "", "password": ""}
    errors: dict[str, str] = {}
    if request.method == "POST":
        values = {
            "employee_number": request.form.get("employee_number", ""),
            "name": request.form.get("name", ""),
            "password": request.form.get("password", ""),
        }
        errors = validate_account_input(values["employee_number"], values["name"], values["password"])
        if not errors:
            role = register_account(
                _get_db(), values["employee_number"], values["name"].strip(), values["password"]
            )
            if role is None:
                errors["employee_number"] = MSG_EMPLOYEE_NUMBER_DUPLICATE
            else:
                flash(MSG_REGISTERED, "message")
                return redirect(url_for("ledger.login"))
    return render_template("register.html", values=values, errors=errors, user=current_user())


@bp.route("/login/", methods=["GET", "POST"])
def login():
    """社員番号とパスワードでログインする。"""
    values = {"employee_number": ""}
    error = None
    if request.method == "POST":
        values["employee_number"] = request.form.get("employee_number", "")
        account = authenticate(
            _get_db(), values["employee_number"], request.form.get("password", "")
        )
        if account is None:
            error = MSG_LOGIN_FAILED
        else:
            log_in_user(account["employee_number"], account["name"], account["role"])
            return redirect(url_for("ledger.status"))
    return render_template("login.html", values=values, error=error, user=current_user())


@bp.post("/logout/")
def logout():
    """ログアウトして貸出状況の画面へ戻す。"""
    log_out_user()
    return redirect(url_for("ledger.status"))


@bp.route("/equipment/new/", methods=["GET", "POST"])
@require_manager
def equipment_new():
    """担当者が備品を登録する。"""
    values = {"equipment_number": "", "name": ""}
    errors: dict[str, str] = {}
    if request.method == "POST":
        values = {
            "equipment_number": request.form.get("equipment_number", ""),
            "name": request.form.get("name", ""),
        }
        errors = validate_equipment_input(values["equipment_number"], values["name"])
        if not errors:
            if register_equipment(_get_db(), values["equipment_number"], values["name"].strip()):
                return redirect(url_for("ledger.status"))
            errors["equipment_number"] = MSG_EQUIPMENT_NUMBER_DUPLICATE
    return render_template(
        "equipment_form.html", mode="new", values=values, errors=errors, user=current_user()
    )


@bp.route("/equipment/<equipment_number>/edit/", methods=["GET", "POST"])
@require_manager
def equipment_edit(equipment_number: str):
    """担当者が備品名を修正する。管理番号は変えられない。"""
    equipment = get_equipment(_get_db(), equipment_number)
    if equipment is None:
        abort(404)
    values = {"equipment_number": equipment["number"], "name": equipment["name"]}
    errors: dict[str, str] = {}
    if request.method == "POST":
        values["name"] = request.form.get("name", "")
        errors = validate_equipment_input(None, values["name"])
        if not errors:
            update_equipment(_get_db(), equipment_number, values["name"].strip())
            return redirect(url_for("ledger.status"))
    return render_template(
        "equipment_form.html", mode="edit", values=values, errors=errors, user=current_user()
    )


@bp.post("/equipment/<equipment_number>/delete/")
@require_manager
def equipment_delete(equipment_number: str):
    """担当者が備品を削除する（記録は残さない）。"""
    if not delete_equipment(_get_db(), equipment_number):
        abort(404)
    return redirect(url_for("ledger.status"))

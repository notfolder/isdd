"""画面と操作の HTTP の受け口。"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from .auth import current_user, log_in_user, log_out_user, require_manager
from .core.accounts import ROLE_MANAGER, authenticate, list_borrower_candidates, register_account
from .core.db import open_connection
from .core.equipment import (
    DELETE_LENT,
    DELETE_MISSING,
    delete_equipment,
    get_equipment,
    list_equipment_status,
    register_equipment,
    update_equipment,
)
from .core.lending import (
    LEND_ALREADY_LENT,
    LEND_NO_BORROWER,
    LEND_NO_EQUIPMENT,
    RETURN_ALREADY,
    RETURN_NO_EQUIPMENT,
    lend_equipment,
    return_equipment,
)
from .core.validation import validate_account_input, validate_equipment_input, validate_lending_input

bp = Blueprint("ledger", __name__)

JST = timezone(timedelta(hours=9))

MSG_LOGIN_FAILED = "社員番号またはパスワードが違います"
MSG_EMPLOYEE_NUMBER_DUPLICATE = "この社員番号は既に登録されています"
MSG_EQUIPMENT_NUMBER_DUPLICATE = "この管理番号は既に使われています"
MSG_REGISTERED = "登録しました。ログインしてください"
MSG_ALREADY_LENT = "この備品は既に貸出中です"
MSG_ALREADY_RETURNED = "この備品は既に返却されています"
MSG_DELETE_LENT = "この備品は貸出中のため削除できません。先に返却を処理してください"
MSG_STALE_EDIT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"


def _get_db():
    """要求ごとの DB 接続を返す。"""
    if "db" not in g:
        g.db = open_connection(current_app.config["DATA_DIR"])
    return g.db


def _today_jst():
    """日本時間の今日の日付。"""
    return datetime.now(JST).date()


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
        "equipment_form.html", mode="new", values=values, errors=errors, error=None, user=current_user()
    )


@bp.route("/equipment/<equipment_number>/edit/", methods=["GET", "POST"])
@require_manager
def equipment_edit(equipment_number: str):
    """担当者が備品名を修正する。管理番号は変えられない。開いた時点と版番号が違えば保存しない。"""
    if request.method == "GET":
        equipment = get_equipment(_get_db(), equipment_number)
        if equipment is None:
            abort(404)
        values = {
            "equipment_number": equipment["number"],
            "name": equipment["name"],
            "revision": equipment["revision"],
        }
        return render_template(
            "equipment_form.html", mode="edit", values=values, errors={}, error=None, user=current_user()
        )

    try:
        revision = int(request.form.get("revision", ""))
    except ValueError:
        revision = -1
    values = {
        "equipment_number": equipment_number,
        "name": request.form.get("name", ""),
        "revision": revision,
    }
    errors = validate_equipment_input(None, values["name"])
    error = None
    if not errors:
        if update_equipment(_get_db(), equipment_number, values["name"].strip(), revision):
            return redirect(url_for("ledger.status"))
        error = MSG_STALE_EDIT
    return render_template(
        "equipment_form.html", mode="edit", values=values, errors=errors, error=error, user=current_user()
    )


@bp.post("/equipment/<equipment_number>/delete/")
@require_manager
def equipment_delete(equipment_number: str):
    """担当者が備品を削除する（記録は残さない）。貸出中の備品は削除しない。"""
    result = delete_equipment(_get_db(), equipment_number)
    if result == DELETE_MISSING:
        abort(404)
    if result == DELETE_LENT:
        flash(MSG_DELETE_LENT, "message")
    return redirect(url_for("ledger.status"))


@bp.route("/equipment/<equipment_number>/lend/", methods=["GET", "POST"])
@require_manager
def equipment_lend(equipment_number: str):
    """担当者が空きの備品を、借りる社員と貸出日で貸し出す。"""
    db = _get_db()
    equipment = get_equipment(db, equipment_number)
    if equipment is None:
        abort(404)
    borrowers = list_borrower_candidates(db)
    values = {"borrower": "", "lent_on": _today_jst().isoformat()}
    errors: dict[str, str] = {}
    if request.method == "POST":
        values = {
            "borrower": request.form.get("borrower", ""),
            "lent_on": request.form.get("lent_on", ""),
        }
        errors = validate_lending_input(values["borrower"], values["lent_on"], _today_jst())
        if not errors:
            result = lend_equipment(db, equipment_number, values["borrower"], values["lent_on"])
            if result == LEND_NO_EQUIPMENT:
                abort(404)
            if result == LEND_ALREADY_LENT:
                flash(MSG_ALREADY_LENT, "message")
                return redirect(url_for("ledger.status"))
            if result == LEND_NO_BORROWER:
                errors["borrower"] = "借りる社員を選んでください"
            else:
                return redirect(url_for("ledger.status"))
    return render_template(
        "lend.html",
        equipment=equipment,
        borrowers=borrowers,
        values=values,
        errors=errors,
        user=current_user(),
    )


@bp.post("/equipment/<equipment_number>/return/")
@require_manager
def equipment_return(equipment_number: str):
    """担当者が返却を処理する。貸出の記録を消して空きに戻す（記録は残さない）。"""
    result = return_equipment(_get_db(), equipment_number)
    if result == RETURN_NO_EQUIPMENT:
        abort(404)
    if result == RETURN_ALREADY:
        flash(MSG_ALREADY_RETURNED, "message")
    return redirect(url_for("ledger.status"))

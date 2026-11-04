"""画面と操作の入口。"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import accounts, auth, equipment

bp = Blueprint("main", __name__)
MSG_EQUIPMENT_NOT_FOUND = "この管理番号の備品は見つかりません"


def _render(template, **context):
    """共通の文脈（ログイン中のアカウントと担当者かどうか）を足して画面を描画する。"""
    account = auth.current_account()
    is_manager = account is not None and account["role"] == accounts.ROLE_MANAGER
    return render_template(template, account=account, is_manager=is_manager, **context)


@bp.route("/")
def index_page():
    """貸出状況の一覧。誰でも見られる。"""
    return _render("index.html", rows=equipment.list_loan_status())


@bp.route("/login/", methods=["GET", "POST"])
def login_page():
    """社員番号とパスワードでログインする。失敗時はどちらが違うかを示さない。"""
    error = None
    employee_number = ""
    if request.method == "POST":
        employee_number = request.form.get("employee_number", "")
        password = request.form.get("password", "")
        account = accounts.authenticate_account(employee_number, password)
        if account is not None:
            auth.login_account(account["id"])
            return redirect(url_for("main.index_page"))
        error = "社員番号またはパスワードが違います"
    return _render("login.html", error=error, employee_number=employee_number)


@bp.route("/logout/", methods=["POST"])
def logout_action():
    """ログアウトして貸出状況の画面へ戻る。"""
    auth.logout_account()
    return redirect(url_for("main.index_page"))


@bp.route("/accounts/register/", methods=["GET", "POST"])
def register_page():
    """社員が自分のアカウントを登録する。成功したらログイン画面で案内する。"""
    values = {"employee_number": "", "name": "", "password": ""}
    errors = {}
    if request.method == "POST":
        values = {
            "employee_number": request.form.get("employee_number", ""),
            "name": request.form.get("name", ""),
            "password": request.form.get("password", ""),
        }
        name = values["name"].strip()
        errors = accounts.validate_registration(values["employee_number"], name, values["password"])
        if not errors:
            _, errors = accounts.register_account(values["employee_number"], name, values["password"])
        if not errors:
            flash("登録しました。ログインしてください")
            return redirect(url_for("main.login_page"))
    return _render("register.html", errors=errors, values=values)


@bp.route("/equipment/new/", methods=["GET", "POST"])
@auth.manager_required
def equipment_new_page():
    """担当者が備品を登録する。"""
    values = {"equipment_number": "", "name": ""}
    errors = {}
    if request.method == "POST":
        values = {
            "equipment_number": request.form.get("equipment_number", ""),
            "name": request.form.get("name", ""),
        }
        name = values["name"].strip()
        errors = equipment.validate_equipment(values["equipment_number"], name)
        if not errors:
            errors = equipment.create_equipment(values["equipment_number"], name)
        if not errors:
            flash("備品を登録しました")
            return redirect(url_for("main.index_page"))
    return _render(
        "equipment_form.html",
        title="備品を登録",
        action=url_for("main.equipment_new_page"),
        errors=errors,
        values=values,
    )


@bp.route("/equipment/<equipment_number>/edit/", methods=["GET", "POST"])
@auth.manager_required
def equipment_edit_page(equipment_number):
    """担当者が備品を修正する。対象が無ければ貸出状況の画面へ戻す。"""
    current = equipment.get_equipment(equipment_number)
    if current is None:
        flash(MSG_EQUIPMENT_NOT_FOUND)
        return redirect(url_for("main.index_page"))
    values = {"equipment_number": current["equipment_number"], "name": current["name"]}
    errors = {}
    if request.method == "POST":
        values = {
            "equipment_number": request.form.get("equipment_number", ""),
            "name": request.form.get("name", ""),
        }
        name = values["name"].strip()
        errors = equipment.validate_equipment(values["equipment_number"], name)
        if not errors:
            try:
                errors = equipment.update_equipment(equipment_number, values["equipment_number"], name)
            except LookupError:
                flash(MSG_EQUIPMENT_NOT_FOUND)
                return redirect(url_for("main.index_page"))
        if not errors:
            flash("備品を修正しました")
            return redirect(url_for("main.index_page"))
    return _render(
        "equipment_form.html",
        title="備品を修正",
        action=url_for("main.equipment_edit_page", equipment_number=equipment_number),
        errors=errors,
        values=values,
    )


@bp.route("/equipment/<equipment_number>/delete/", methods=["POST"])
@auth.manager_required
def equipment_delete_action(equipment_number):
    """担当者が備品を削除する（確認は画面側で行う）。"""
    if equipment.delete_equipment(equipment_number):
        flash("備品を削除しました")
    else:
        flash(MSG_EQUIPMENT_NOT_FOUND)
    return redirect(url_for("main.index_page"))

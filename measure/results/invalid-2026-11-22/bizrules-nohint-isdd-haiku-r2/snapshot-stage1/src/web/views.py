"""画面のルーティングと描画。入力を読み、業務層を呼び、結果を画面に返す。業務ルールはここに書かない。"""

from flask import current_app, flash, redirect, render_template, request, url_for

from service.accounts import User
from service.errors import NotFoundError, ServiceError
from service.clock import today_jst
from service.permissions import require_manager
from web.auth import current_user, end_session, start_session

TOP_ENDPOINT = "status_page"


def _services():
    return current_app.extensions["services"]


def _manager_or_redirect():
    """担当者なら (利用者, None) を返す。未ログインならログイン画面への転送、社員なら PermissionDenied。"""
    user = current_user()
    if user is None:
        return None, redirect(url_for("login_page"))
    require_manager(user)
    return user, None


def _equipment_form_values(form) -> dict[str, str]:
    return {"equipment_number": form.get("equipment_number", ""), "name": form.get("name", "")}


def status_page():
    """貸出状況（トップ）。ログイン不要。"""
    rows = _services().equipment.list_status()
    return render_template("status.html", rows=rows)


def register_account_page():
    """アカウント登録。成功したらログイン画面へ移り、案内を出す。"""
    values = {"employee_number": "", "name": "", "password": ""}
    errors: dict[str, str] = {}
    message = ""
    if request.method == "POST":
        values = {key: request.form.get(key, "") for key in values}
        try:
            _services().accounts.register(values["employee_number"], values["name"], values["password"])
        except ServiceError as error:
            errors = error.field_errors
            message = error.message
        else:
            flash("登録しました。ログインしてください", "message")
            return redirect(url_for("login_page"))
    return render_template("register_account.html", values=values, errors=errors, error=message)


def login_page():
    """ログイン。成功したら貸出状況へ移る。"""
    values = {"employee_number": "", "password": ""}
    message = ""
    if request.method == "POST":
        values = {key: request.form.get(key, "") for key in values}
        try:
            user: User = _services().accounts.authenticate(values["employee_number"], values["password"])
        except ServiceError as error:
            message = error.message
        else:
            start_session(user)
            return redirect(url_for(TOP_ENDPOINT))
    return render_template("login.html", values=values, error=message)


def logout():
    """ログアウト（POST のみ）。貸出状況へ戻り、案内を出す。"""
    end_session()
    flash("ログアウトしました", "message")
    return redirect(url_for(TOP_ENDPOINT))


def equipment_new_page():
    """備品の登録（担当者だけ）。"""
    user, redirect_response = _manager_or_redirect()
    if redirect_response is not None:
        return redirect_response
    values = {"equipment_number": "", "name": ""}
    errors: dict[str, str] = {}
    message = ""
    if request.method == "POST":
        values = _equipment_form_values(request.form)
        try:
            _services().equipment.register(user, values["equipment_number"], values["name"])
        except ServiceError as error:
            errors, message = error.field_errors, error.message
        else:
            flash("備品を登録しました", "message")
            return redirect(url_for(TOP_ENDPOINT))
    return render_template("equipment_form.html", title="備品の登録", action=url_for("equipment_new_page"),
                           values=values, errors=errors, error=message)


def equipment_edit_page(equipment_id: int):
    """備品の修正（担当者だけ）。修正前の値を初期表示する。"""
    user, redirect_response = _manager_or_redirect()
    if redirect_response is not None:
        return redirect_response
    action = url_for("equipment_edit_page", equipment_id=equipment_id)
    errors: dict[str, str] = {}
    message = ""
    if request.method == "POST":
        values = _equipment_form_values(request.form)
        try:
            _services().equipment.update(user, equipment_id, values["equipment_number"], values["name"])
        except ServiceError as error:
            errors, message = error.field_errors, error.message
        else:
            flash("備品を修正しました", "message")
            return redirect(url_for(TOP_ENDPOINT))
    else:
        item = _services().equipment.get(equipment_id)
        values = {"equipment_number": item.equipment_number, "name": item.name}
    return render_template("equipment_form.html", title="備品の修正", action=action,
                           values=values, errors=errors, error=message)


def equipment_delete(equipment_id: int):
    """備品の削除（担当者だけ、POST のみ）。貸出中なら削除せず理由を出す。"""
    user, redirect_response = _manager_or_redirect()
    if redirect_response is not None:
        return redirect_response
    try:
        _services().equipment.delete(user, equipment_id)
    except ServiceError as error:
        flash(error.message, "error")
    else:
        flash("備品を削除しました", "message")
    return redirect(url_for(TOP_ENDPOINT))


def _lending_form(equipment_id: int, values: dict[str, str], errors: dict[str, str], message: str):
    item = _services().equipment.get(equipment_id)
    borrowers = _services().accounts.list_borrowers()
    return render_template("lending_form.html", item=item, borrowers=borrowers, values=values,
                           errors=errors, error=message, today=today_jst().isoformat())


def lending_new_page():
    """貸出の登録（担当者だけ）。備品は ?equipment= で指定し、POST では隠し欄 equipment で送る。"""
    user, redirect_response = _manager_or_redirect()
    if redirect_response is not None:
        return redirect_response
    raw_id = request.form.get("equipment") if request.method == "POST" else request.args.get("equipment")
    if raw_id is None or not raw_id.isdigit():
        raise NotFoundError("備品が指定されていません")
    equipment_id = int(raw_id)
    values = {"borrower": "", "lent_on": today_jst().isoformat()}
    errors: dict[str, str] = {}
    message = ""
    if request.method == "POST":
        values = {"borrower": request.form.get("borrower", ""), "lent_on": request.form.get("lent_on", "")}
        try:
            _services().lending.lend(user, equipment_id, values["borrower"], values["lent_on"], today_jst())
        except ServiceError as error:
            errors, message = error.field_errors, error.message
        else:
            flash("貸出を登録しました", "message")
            return redirect(url_for(TOP_ENDPOINT))
    return _lending_form(equipment_id, values, errors, message)


def lending_return(equipment_id: int):
    """返却（担当者だけ、POST のみ）。貸出記録を消して空きに戻す。"""
    user, redirect_response = _manager_or_redirect()
    if redirect_response is not None:
        return redirect_response
    try:
        _services().lending.return_equipment(user, equipment_id)
    except ServiceError as error:
        flash(error.message, "error")
    else:
        flash("返却を記録しました", "message")
    return redirect(url_for(TOP_ENDPOINT))


def register_routes(app) -> None:
    """画面の URL を関数に結ぶ。URL は契約（contract.md）の表と、貸出の画面の自由な URL。"""
    app.add_url_rule("/", "status_page", status_page, methods=["GET"])
    app.add_url_rule("/accounts/register/", "register_account_page", register_account_page,
                     methods=["GET", "POST"])
    app.add_url_rule("/login/", "login_page", login_page, methods=["GET", "POST"])
    app.add_url_rule("/logout/", "logout", logout, methods=["POST"])
    app.add_url_rule("/equipment/new/", "equipment_new_page", equipment_new_page, methods=["GET", "POST"])
    app.add_url_rule("/equipment/<int:equipment_id>/edit/", "equipment_edit_page", equipment_edit_page,
                     methods=["GET", "POST"])
    app.add_url_rule("/equipment/<int:equipment_id>/delete/", "equipment_delete", equipment_delete,
                     methods=["POST"])
    app.add_url_rule("/lendings/new/", "lending_new_page", lending_new_page, methods=["GET", "POST"])
    app.add_url_rule("/lendings/<int:equipment_id>/return/", "lending_return", lending_return,
                     methods=["POST"])

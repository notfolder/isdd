"""画面の経路と画面の処理。

入力を受け、担当者の判定を通してから業務処理を呼ぶ。業務ルール違反は、入力欄のエラー、
画面全体のエラー（.error）、操作の知らせ（.message）のどれかに振り分けて表示する。
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from . import accounts, auth, db, equipment, loans
from .errors import RuleViolation
from .timeutil import today_jst
from .validation import validate_equipment_input, validate_lent_on, validate_password, validate_account_input

bp = Blueprint("ledger", __name__)


def _get_db():
    """この要求で使うデータベース接続を返す（要求の終わりに閉じる）。"""
    if "db" not in g:
        g.db = db.connect(current_app.config["DATA_DIR"])
    return g.db


@bp.teardown_request
def _close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@bp.before_request
def _load_current_user():
    """cookie のセッションからログイン中の社員を求め、g.current_user に入れる。"""
    g.current_user = None
    g.drop_session_cookie = False
    token = request.cookies.get(auth.SESSION_COOKIE)
    if token:
        g.current_user = auth.resolve_session_user(
            _get_db(), token, current_app.config["SESSION_IDLE_TIMEOUT_SECONDS"]
        )
        if g.current_user is None:
            g.drop_session_cookie = True


@bp.after_request
def _drop_stale_cookie(response):
    if g.get("drop_session_cookie"):
        response.delete_cookie(auth.SESSION_COOKIE)
    return response


def _render(template: str, status: int = 200, **context):
    return render_template(template, current_user=g.current_user, **context), status


def _conflict_to_status(violation: RuleViolation):
    """業務例外を、貸出状況の画面の知らせ（.message か .error）に変えて貸出状況へ戻す。"""
    flash(violation.message, violation.level)
    return redirect(url_for("ledger.lending_status"))


def _manager_form_version(form_key: str = "version") -> int:
    """フォームの版番号を整数で返す。不正な値は 0（どの版とも一致しない）にする。"""
    try:
        return int(request.form.get(form_key, ""))
    except ValueError:
        return 0


@bp.get("/")
def lending_status():
    """貸出状況（トップ）。誰でも見られる。"""
    rows = equipment.list_lending_status(_get_db())
    return _render("status.html", rows=rows)


@bp.route("/accounts/register/", methods=["GET", "POST"])
def account_register():
    """アカウント登録。最初の 1 件は担当者、以降は社員。"""
    values = {"employee_number": "", "name": ""}
    if request.method == "POST":
        employee_number = request.form.get("employee_number", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        values = {"employee_number": employee_number, "name": name}
        errors = validate_account_input(employee_number, name, password)
        if not errors:
            try:
                accounts.register_account(_get_db(), employee_number, name, password)
            except RuleViolation as violation:
                errors[violation.field or "employee_number"] = violation.message
        if errors:
            return _render("account_register.html", status=200, errors=errors, values=values)
        flash("登録しました。ログインしてください", "message")
        return redirect(url_for("ledger.login"))
    return _render("account_register.html", errors={}, values=values)


@bp.route("/login/", methods=["GET", "POST"])
def login():
    """ログイン。失敗しても、社員番号とパスワードのどちらが違うかは示さない。"""
    if request.method == "POST":
        employee_number = request.form.get("employee_number", "").strip()
        password = request.form.get("password", "")
        authenticated = accounts.authenticate(_get_db(), employee_number, password)
        if authenticated is not None:
            token = auth.create_session(_get_db(), authenticated)
            response = redirect(url_for("ledger.lending_status"))
            response.set_cookie(
                auth.SESSION_COOKIE, token, httponly=True, samesite="Lax", path="/"
            )
            return response
        return _render(
            "login.html",
            status=200,
            error="社員番号またはパスワードが違います",
            values={"employee_number": employee_number},
        )
    return _render("login.html", error=None, values={"employee_number": ""})


@bp.post("/logout/")
def logout():
    """ログアウト（セッションを消し、cookie を削除する）。"""
    token = request.cookies.get(auth.SESSION_COOKIE)
    auth.delete_session(_get_db(), token)
    response = redirect(url_for("ledger.lending_status"))
    response.delete_cookie(auth.SESSION_COOKIE)
    return response


@bp.route("/equipment/new/", methods=["GET", "POST"])
@auth.require_manager
def equipment_new():
    """備品の登録（担当者だけ）。"""
    values = {"equipment_number": "", "name": ""}
    if request.method == "POST":
        number = request.form.get("equipment_number", "").strip()
        name = request.form.get("name", "").strip()
        values = {"equipment_number": number, "name": name}
        errors = validate_equipment_input(number, name)
        if not errors:
            try:
                equipment.create_equipment(_get_db(), number, name)
            except RuleViolation as violation:
                errors[violation.field or "equipment_number"] = violation.message
        if errors:
            return _render("equipment_form.html", errors=errors, values=values, heading="備品の登録", equipment_version=None, editing=False)
        flash("備品を登録しました", "message")
        return redirect(url_for("ledger.lending_status"))
    return _render("equipment_form.html", errors={}, values=values, heading="備品の登録", equipment_version=None, editing=False)


@bp.route("/equipment/<equipment_number>/edit/", methods=["GET", "POST"])
@auth.require_manager
def equipment_edit(equipment_number: str):
    """備品の修正（担当者だけ）。版番号が一致しなければ、他の担当者の先行更新として拒否する。"""
    current = equipment.get_equipment(_get_db(), equipment_number)
    if request.method == "POST":
        if current is None or current["version"] != _manager_form_version():
            return _conflict_to_status(RuleViolation(equipment.CONFLICT_MESSAGE, level="error"))
        number = request.form.get("equipment_number", "").strip()
        name = request.form.get("name", "").strip()
        values = {"equipment_number": number, "name": name}
        errors = validate_equipment_input(number, name)
        if not errors:
            try:
                equipment.update_equipment(_get_db(), equipment_number, number, name, _manager_form_version())
            except RuleViolation as violation:
                if violation.field is None:
                    return _conflict_to_status(violation)
                errors[violation.field] = violation.message
        if errors:
            return _render("equipment_form.html", errors=errors, values=values, heading="備品の修正", equipment_version=_manager_form_version(), editing=True)
        flash("備品を更新しました", "message")
        return redirect(url_for("ledger.lending_status"))
    if current is None:
        return _conflict_to_status(RuleViolation(equipment.CONFLICT_MESSAGE, level="error"))
    values = {"equipment_number": current["equipment_number"], "name": current["name"]}
    return _render("equipment_form.html", errors={}, values=values, heading="備品の修正", equipment_version=current["version"], editing=True)


@bp.post("/equipment/<equipment_number>/delete/")
@auth.require_manager
def equipment_delete(equipment_number: str):
    """備品の削除（担当者だけ）。貸出中と、他の担当者の先行更新は拒否する。"""
    try:
        equipment.delete_equipment(_get_db(), equipment_number, _manager_form_version())
    except RuleViolation as violation:
        return _conflict_to_status(violation)
    flash("備品を削除しました", "message")
    return redirect(url_for("ledger.lending_status"))


@bp.route("/equipment/<equipment_number>/lend/", methods=["GET", "POST"])
@auth.require_manager
def lend(equipment_number: str):
    """貸出の登録（担当者だけ）。借りる社員と貸出日を入力する。"""
    conn = _get_db()
    current = equipment.get_equipment(conn, equipment_number)
    if current is None:
        return _conflict_to_status(RuleViolation(equipment.CONFLICT_MESSAGE, level="error"))
    borrowers = accounts.list_accounts(conn)
    if request.method == "POST":
        borrower = request.form.get("borrower", "").strip()
        lent_on = request.form.get("lent_on", "").strip()
        values = {"borrower": borrower, "lent_on": lent_on}
        errors: dict[str, str] = {}
        if not borrower:
            errors["borrower"] = "借りる社員を選んでください"
        date_error = validate_lent_on(lent_on, today_jst())
        if date_error:
            errors["lent_on"] = date_error
        if not errors:
            try:
                loans.lend_equipment(conn, equipment_number, _manager_form_version(), borrower, lent_on)
            except RuleViolation as violation:
                if violation.field is None:
                    return _conflict_to_status(violation)
                errors[violation.field] = violation.message
            else:
                flash("貸出を登録しました", "message")
                return redirect(url_for("ledger.lending_status"))
        return _render("lend_form.html", errors=errors, values=values, equipment=current, borrowers=borrowers, equipment_version=_manager_form_version())
    return _render("lend_form.html", errors={}, values={"borrower": "", "lent_on": today_jst()}, equipment=current, borrowers=borrowers, equipment_version=current["version"])


@bp.post("/equipment/<equipment_number>/return/")
@auth.require_manager
def return_equipment_view(equipment_number: str):
    """返却の登録（担当者だけ）。貸出の記録を消す。"""
    try:
        loans.return_equipment(_get_db(), equipment_number, _manager_form_version())
    except RuleViolation as violation:
        return _conflict_to_status(violation)
    flash("返却を登録しました", "message")
    return redirect(url_for("ledger.lending_status"))


@bp.get("/accounts/")
@auth.require_manager
def account_list():
    """アカウントの一覧（担当者だけ）。?reset=社員番号 で、その行にパスワード再設定の入力欄を出す。"""
    rows = accounts.list_accounts(_get_db())
    return _render("account_list.html", rows=rows, reset=request.args.get("reset", ""), reset_error=None)


@bp.post("/accounts/<employee_number>/manager/")
@auth.require_manager
def account_manager(employee_number: str):
    """担当者にする（action=grant）か、担当者から外す（action=revoke）。"""
    grant = request.form.get("action") == "grant"
    try:
        accounts.set_manager_role(_get_db(), employee_number, grant)
    except RuleViolation as violation:
        flash(violation.message, violation.level)
        return redirect(url_for("ledger.account_list"))
    flash("担当者を変更しました", "message")
    return redirect(url_for("ledger.account_list"))


@bp.post("/accounts/<employee_number>/password/")
@auth.require_manager
def account_password(employee_number: str):
    """パスワードの再設定（担当者だけ）。8 文字未満は入力欄のエラーにする。"""
    new_password = request.form.get("new_password", "")
    error = validate_password(new_password)
    if error:
        rows = accounts.list_accounts(_get_db())
        return _render("account_list.html", rows=rows, reset=employee_number, reset_error=error)
    try:
        accounts.reset_password(_get_db(), employee_number, new_password)
    except RuleViolation as violation:
        flash(violation.message, violation.level)
        return redirect(url_for("ledger.account_list"))
    flash("パスワードを再設定しました", "message")
    return redirect(url_for("ledger.account_list"))


@bp.post("/accounts/<employee_number>/delete/")
@auth.require_manager
def account_delete(employee_number: str):
    """アカウントの削除（担当者だけ）。貸出中の社員と担当者 0 人になる削除は拒否する。"""
    try:
        accounts.delete_account(_get_db(), employee_number)
    except RuleViolation as violation:
        flash(violation.message, violation.level)
        return redirect(url_for("ledger.account_list"))
    flash("アカウントを削除しました", "message")
    return redirect(url_for("ledger.account_list"))

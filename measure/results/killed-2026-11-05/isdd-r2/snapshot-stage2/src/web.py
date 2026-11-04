"""画面と経路の定義、Flask アプリの作成。"""

from flask import (
    Blueprint,
    Flask,
    current_app,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from src import accounts, auth, db, equipment, lending, sessions, validation

bp = Blueprint("ledger", __name__)

SESSION_COOKIE = "sid"
NOTICE_MESSAGES = {
    "registered": "登録しました。ログインしてください",
    "manager_only": "この操作は担当者だけが行えます",
    "not_found": "備品が見つかりません",
    "deleted": "備品を削除しました",
    "delete_lent": "この備品は貸出中のため削除できません。先に返却を処理してください",
    "lent": "貸出を登録しました",
    "already_lent": "この備品は既に貸出中です",
    "returned": "返却を処理しました",
    "already_returned": "この備品は既に返却されています",
}
STATUS_NOTICE_KEYS = (
    "manager_only",
    "not_found",
    "deleted",
    "delete_lent",
    "lent",
    "already_lent",
    "returned",
    "already_returned",
)
MSG_CONFLICT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
ACCOUNT_FIELDS = ("employee_number", "name", "password")
EQUIPMENT_FIELDS = ("equipment_number", "name")


def _conn():
    """このリクエストの DB 接続を返す。無ければ開く。"""
    if "db" not in g:
        g.db = db.connect(current_app.config["DATA_DIR"])
    return g.db


def _current_user():
    """Cookie のトークンから現在の利用者を返す。未ログインなら None。"""
    return auth.current_user(
        _conn(),
        request.cookies.get(SESSION_COOKIE),
        current_app.config["SESSION_IDLE_TIMEOUT_SECONDS"],
    )


def _notice_from_query(allowed):
    """クエリの notice を、許可された知らせの文言に変換する。許可されない値は None。"""
    key = request.args.get("notice", "")
    if key in allowed:
        return NOTICE_MESSAGES[key]
    return None


def _guard_manager(user):
    """担当者以外の操作を止める。止める場合は転送の応答、通す場合は None を返す。"""
    access = auth.require_manager(user)
    if access == auth.ACCESS_LOGIN_REQUIRED:
        return redirect(url_for("ledger.login"))
    if access == auth.ACCESS_MANAGER_ONLY:
        return redirect(url_for("ledger.equipment_status", notice="manager_only"))
    return None


@bp.get("/")
def equipment_status():
    """貸出状況の画面。誰でも見られる。ログインの状態に応じてボタンを出す。"""
    user = _current_user()
    rows = equipment.list_equipment(_conn())
    return render_template(
        "status.html",
        user=user,
        is_manager=auth.require_manager(user) == auth.ACCESS_OK,
        rows=rows,
        notice=_notice_from_query(STATUS_NOTICE_KEYS),
    )


@bp.route("/accounts/register/", methods=["GET", "POST"])
def account_register():
    """アカウント登録の画面と登録。成功したらログイン画面へ移す。"""
    if request.method == "GET":
        return render_template("register.html", errors={}, values=dict.fromkeys(ACCOUNT_FIELDS, ""))
    values = {field: request.form.get(field, "") for field in ACCOUNT_FIELDS}
    employee_number = values["employee_number"].strip()
    name = values["name"].strip()
    password = values["password"]
    errors = validation.validate_account_input(employee_number, name, password)
    if not errors:
        errors, _role = accounts.register_account(_conn(), employee_number, name, password)
    if errors:
        return render_template("register.html", errors=errors, values=values)
    return redirect(url_for("ledger.login", notice="registered"))


@bp.route("/login/", methods=["GET", "POST"])
def login():
    """ログインの画面と照合。失敗時はどちらが違うかを示さない。"""
    if request.method == "GET":
        return render_template(
            "login.html",
            error=None,
            notice=_notice_from_query(("registered",)),
            values={"employee_number": "", "password": ""},
        )
    employee_number = request.form.get("employee_number", "").strip()
    password = request.form.get("password", "")
    if accounts.verify_login(_conn(), employee_number, password):
        token = sessions.create_session(_conn(), employee_number)
        response = redirect(url_for("ledger.equipment_status"))
        response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="Lax", path="/")
        return response
    return render_template(
        "login.html",
        error="社員番号またはパスワードが違います",
        notice=None,
        values={"employee_number": employee_number, "password": password},
    )


@bp.post("/logout/")
def logout():
    """ログアウト。セッションを削除し、Cookie を消す。"""
    sessions.delete_session(_conn(), request.cookies.get(SESSION_COOKIE))
    response = redirect(url_for("ledger.equipment_status"))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@bp.route("/equipment/new/", methods=["GET", "POST"])
def equipment_new():
    """備品の登録の画面と登録。担当者だけが使える。"""
    refused = _guard_manager(_current_user())
    if refused is not None:
        return refused
    if request.method == "GET":
        return render_template(
            "equipment_form.html",
            heading="備品の登録",
            action=url_for("ledger.equipment_new"),
            errors={},
            values=dict.fromkeys(EQUIPMENT_FIELDS, ""),
            loaded_updated_at=None,
            form_error=None,
        )
    values = {field: request.form.get(field, "") for field in EQUIPMENT_FIELDS}
    number = values["equipment_number"].strip()
    name = values["name"].strip()
    errors = validation.validate_equipment_input(number, name)
    if not errors:
        errors, _status = equipment.create_equipment(_conn(), number, name)
    if errors:
        return render_template(
            "equipment_form.html",
            heading="備品の登録",
            action=url_for("ledger.equipment_new"),
            errors=errors,
            values=values,
            loaded_updated_at=None,
            form_error=None,
        )
    return redirect(url_for("ledger.equipment_status"))


@bp.route("/equipment/<equipment_number>/edit/", methods=["GET", "POST"])
def equipment_edit(equipment_number):
    """備品の修正の画面と保存。担当者だけが使える。存在しない備品は貸出状況へ戻す。

    画面を開いた時点の更新時刻を隠し項目で持ち、保存時に他の担当者の更新・削除を検知する。
    """
    refused = _guard_manager(_current_user())
    if refused is not None:
        return refused
    action = url_for("ledger.equipment_edit", equipment_number=equipment_number)
    if request.method == "GET":
        item = equipment.get_equipment(_conn(), equipment_number)
        if item is None:
            return redirect(url_for("ledger.equipment_status", notice="not_found"))
        values = {"equipment_number": item["equipment_number"], "name": item["name"]}
        return render_template(
            "equipment_form.html",
            heading="備品の修正",
            action=action,
            errors={},
            values=values,
            loaded_updated_at=item["updated_at"],
            form_error=None,
        )
    loaded_updated_at = request.form.get("loaded_updated_at", "")
    values = {field: request.form.get(field, "") for field in EQUIPMENT_FIELDS}
    number = values["equipment_number"].strip()
    name = values["name"].strip()
    errors = validation.validate_equipment_input(number, name)
    form_error = None
    if not errors:
        errors, status = equipment.update_equipment(
            _conn(), equipment_number, number, name, loaded_updated_at
        )
        if status == equipment.STATUS_CONFLICT:
            form_error = MSG_CONFLICT
    if errors or form_error:
        return render_template(
            "equipment_form.html",
            heading="備品の修正",
            action=action,
            errors=errors,
            values=values,
            loaded_updated_at=loaded_updated_at,
            form_error=form_error,
        )
    return redirect(url_for("ledger.equipment_status"))


@bp.post("/equipment/<equipment_number>/delete/")
def equipment_delete(equipment_number):
    """備品の削除。担当者だけが行える。貸出中の備品は削除しない。削除の記録は残さない。"""
    refused = _guard_manager(_current_user())
    if refused is not None:
        return refused
    status = equipment.delete_equipment(_conn(), equipment_number)
    if status == equipment.STATUS_NOT_FOUND:
        return redirect(url_for("ledger.equipment_status", notice="not_found"))
    if status == equipment.STATUS_LENT:
        return redirect(url_for("ledger.equipment_status", notice="delete_lent"))
    return redirect(url_for("ledger.equipment_status", notice="deleted"))


@bp.route("/equipment/<equipment_number>/lend/", methods=["GET", "POST"])
def equipment_lend(equipment_number):
    """貸出の登録の画面と登録。担当者だけが使える。借りる社員と貸出日を記録する。"""
    refused = _guard_manager(_current_user())
    if refused is not None:
        return refused
    item = equipment.get_equipment(_conn(), equipment_number)
    if item is None:
        return redirect(url_for("ledger.equipment_status", notice="not_found"))
    action = url_for("ledger.equipment_lend", equipment_number=equipment_number)
    if request.method == "GET":
        values = {"borrower": "", "lent_on": lending.today_jst().isoformat()}
        return render_template(
            "lending_form.html",
            item=item,
            action=action,
            borrowers=accounts.list_borrowers(_conn()),
            errors={},
            values=values,
        )
    values = {
        "borrower": request.form.get("borrower", ""),
        "lent_on": request.form.get("lent_on", ""),
    }
    errors = validation.validate_lending_input(
        values["borrower"].strip(), values["lent_on"].strip(), lending.today_jst()
    )
    if not errors:
        errors, status = lending.lend_equipment(
            _conn(), equipment_number, values["borrower"].strip(), values["lent_on"].strip()
        )
        if status == lending.STATUS_NOT_FOUND:
            return redirect(url_for("ledger.equipment_status", notice="not_found"))
        if status == lending.STATUS_ALREADY_LENT:
            return redirect(url_for("ledger.equipment_status", notice="already_lent"))
        if status == lending.STATUS_OK:
            return redirect(url_for("ledger.equipment_status", notice="lent"))
    return render_template(
        "lending_form.html",
        item=item,
        action=action,
        borrowers=accounts.list_borrowers(_conn()),
        errors=errors,
        values=values,
    )


@bp.post("/equipment/<equipment_number>/return/")
def equipment_return(equipment_number):
    """備品の返却。担当者だけが行える。貸出の行を消し、空きに戻す（記録は残さない）。"""
    refused = _guard_manager(_current_user())
    if refused is not None:
        return refused
    status = lending.return_equipment(_conn(), equipment_number)
    if status == lending.STATUS_NOT_FOUND:
        return redirect(url_for("ledger.equipment_status", notice="not_found"))
    if status == lending.STATUS_NOT_LENT:
        return redirect(url_for("ledger.equipment_status", notice="already_returned"))
    return redirect(url_for("ledger.equipment_status", notice="returned"))


def _close_db(_exc):
    """リクエストの終わりに DB 接続を閉じる。"""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def create_app(settings):
    """Flask アプリを作る。DB が無ければスキーマを作る。

    引数 settings は src.config.load_settings の戻り値の辞書。
    戻り値は Flask アプリ。
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["DATA_DIR"] = settings["data_dir"]
    app.config["SESSION_IDLE_TIMEOUT_SECONDS"] = settings["session_idle_timeout_seconds"]
    conn = db.connect(settings["data_dir"])
    try:
        db.init_schema(conn)
    finally:
        conn.close()
    app.register_blueprint(bp)
    app.teardown_appcontext(_close_db)
    return app

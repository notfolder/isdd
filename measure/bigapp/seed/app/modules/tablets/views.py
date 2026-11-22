"""タブレットの貸出の画面と操作。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import current_user, login_required, staff_required
from app.core.db import get_db
from app.modules.tablets import bp
from app.modules.tablets.models import LendingRules


def _open_loan(item_code):
    """物の貸出中の記録。無ければ None。"""
    return get_db().execute(
        "SELECT * FROM tablets_loans WHERE item_code = ? AND returned_on IS NULL", (item_code,)
    ).fetchone()


def _item(code):
    return get_db().execute("SELECT * FROM tablets_items WHERE code = ?", (code,)).fetchone()


def _rows(q=""):
    """一覧の行。番号か名前の一部で絞り込める。"""
    rules = LendingRules(clock.today())
    items = get_db().execute(
        "SELECT * FROM tablets_items WHERE code LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' ORDER BY code",
        (_like(q), _like(q)),
    ).fetchall()
    rows = []
    for item in items:
        loan = _open_loan(item["code"])
        rows.append({
            "code": item["code"],
            "name": item["name"],
            "status": rules.status(loan),
            "borrower": loan["employee_no"] if loan else None,
            "lent_on": loan["lent_on"] if loan else None,
            "due_on": loan["due_on"] if loan else None,
        })
    return rows


def _like(q):
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _page(error=None, q=""):
    status = 400 if error else 200
    return render_template("tablets/index.html", rows=_rows(q), q=q, error=error), status


def _done(action, target):
    audit.record("tablets", action, target)
    get_db().commit()
    return redirect(url_for("tablets.index"))


@bp.route("/")
@login_required
def index():
    return _page(q=request.args.get("q", "").strip())


@bp.route("/items/new", methods=["POST"])
@staff_required
def item_create():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not code:
        return _page("番号を入力してください")
    if not name:
        return _page("名前を入力してください")
    if _item(code) is not None:
        return _page("この番号は既に登録されています")
    get_db().execute("INSERT INTO tablets_items (code, name) VALUES (?, ?)", (code, name))
    return _done("item_create", code)


@bp.route("/items/edit", methods=["POST"])
@staff_required
def item_update():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if _item(code) is None:
        return _page("物が見つかりません")
    if not name:
        return _page("名前を入力してください")
    get_db().execute("UPDATE tablets_items SET name = ? WHERE code = ?", (name, code))
    return _done("item_update", code)


@bp.route("/items/delete", methods=["POST"])
@staff_required
def item_delete():
    code = request.form.get("code", "").strip()
    if _item(code) is None:
        return _page("物が見つかりません")
    if _open_loan(code) is not None:
        return _page("貸出中の物は削除できません")
    get_db().execute("DELETE FROM tablets_items WHERE code = ?", (code,))
    return _done("item_delete", code)


@bp.route("/lend", methods=["POST"])
@staff_required
def lend():
    form = request.form
    code, number = form.get("item_code", "").strip(), form.get("employee_no", "").strip()
    rules = LendingRules(clock.today())
    if _item(code) is None:
        return _page("物が見つかりません")
    if _open_loan(code) is not None:
        return _page("貸出中の物は貸し出せません")
    conn = get_db()
    employee = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone()
    open_loans = conn.execute(
        "SELECT * FROM tablets_loans WHERE employee_no = ? AND returned_on IS NULL", (number,)
    ).fetchall()
    error = rules.check_borrower(employee, open_loans)
    if error:
        return _page(error)
    lent_on, error = rules.parse_lent_on(form.get("lent_on"))
    if error:
        return _page(error)
    conn.execute(
        "INSERT INTO tablets_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, number, lent_on.isoformat(), rules.due_on(lent_on).isoformat()),
    )
    return _done("lend", f"{code}:{number}")


@bp.route("/return", methods=["POST"])
@staff_required
def return_item():
    code = request.form.get("item_code", "").strip()
    if _item(code) is None:
        return _page("物が見つかりません")
    loan = _open_loan(code)
    if loan is None:
        return _page("貸出中ではありません")
    get_db().execute(
        "UPDATE tablets_loans SET returned_on = ? WHERE id = ?", (clock.today().isoformat(), loan["id"])
    )
    return _done("return", code)


@bp.route("/history")
@login_required
def history():
    rows = get_db().execute(
        "SELECT * FROM tablets_loans WHERE returned_on IS NOT NULL ORDER BY returned_on DESC, id DESC"
    ).fetchall()
    return render_template("tablets/history.html", rows=rows)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"items": _rows()})

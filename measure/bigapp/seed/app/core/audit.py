"""操作の記録。データを変える操作は、どの機能でも record() で 1 行残す（総務規程 第 7 条）。"""

from flask import Blueprint, jsonify, render_template

from app.core import clock
from app.core.auth import current_user, staff_required
from app.core.db import get_db

bp = Blueprint("audit", __name__)


def record(module: str, action: str, target: str = "") -> None:
    """操作を 1 行残す。呼び出し側のトランザクションに乗る（commit は呼び出し側）。"""
    user = current_user()
    get_db().execute(
        "INSERT INTO audit_log (logged_at, actor_no, module, action, target) VALUES (?, ?, ?, ?, ?)",
        (clock.now_text(), user["employee_no"] if user else None, module, action, target),
    )


def _rows():
    return get_db().execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 500").fetchall()


@bp.route("/audit/")
@staff_required
def index():
    return render_template("audit.html", rows=_rows())


@bp.route("/audit.json")
@staff_required
def index_json():
    return jsonify({"rows": [dict(r) for r in get_db().execute("SELECT * FROM audit_log ORDER BY id").fetchall()]})

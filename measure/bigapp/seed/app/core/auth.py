"""ログインと権限。役割は staff（総務の担当者）と employee（社員）。"""

import functools

from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.core.db import get_db

bp = Blueprint("auth", __name__)


def current_user():
    """ログイン中の社員の行。ログインしていなければ None。"""
    if "user" not in g:
        number = session.get("employee_no")
        g.user = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (number,)).fetchone() if number else None
    return g.user


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def staff_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return redirect(url_for("auth.login"))
        if user["role"] != "staff":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@bp.app_context_processor
def inject_user():
    return {"current_user": current_user()}


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        row = get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (request.form.get("employee_no", ""),)).fetchone()
        if row is None or row["status"] != "active" or not check_password_hash(row["password_hash"], request.form.get("password", "")):
            error = "社員番号またはパスワードが違います"
        else:
            session.clear()
            session["employee_no"] = row["employee_no"]
            return redirect(url_for("home.index"))
    return render_template("login.html", error=error), (400 if error else 200)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

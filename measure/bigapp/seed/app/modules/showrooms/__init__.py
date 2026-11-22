"""ショールームの予約。部屋の登録、予約、取消、日ごとの表を扱う。"""

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db

from . import logic

TITLE = "ショールームの予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS showrooms_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS showrooms_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES showrooms_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start_min INTEGER NOT NULL,
    end_min INTEGER NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("showrooms", __name__, url_prefix="/showrooms", template_folder="templates")


def _index_page(error=None, status=200):
    date = request.args.get("date", "").strip()
    return render_template(
        "showrooms/index.html", rooms=logic.list_rooms(), bookings=logic.list_bookings(date or None), date=date, error=error
    ), status


def _apply(action, func, *args):
    """操作を行い、記録を残して一覧へ戻る。受け付けないときは 400 で理由を出す。"""
    try:
        target = func(*args)
    except logic.InputError as e:
        get_db().rollback()
        return _index_page(str(e), 400)
    audit.record("showrooms", action, target)
    get_db().commit()
    return redirect("/showrooms/")


@bp.route("/")
@login_required
def index():
    date = request.args.get("date", "").strip()
    if date:
        try:
            logic.parse_date(date)
        except logic.InputError as e:
            return _index_page(str(e), 400)
    return _index_page()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    f = request.form
    return _apply("room_create", logic.create_room, f.get("code"), f.get("name"))


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    f = request.form
    return _apply("room_update", logic.update_room, f.get("code"), f.get("name"))


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    f = request.form
    return _apply("book", logic.book, f.get("room_code"), f.get("employee_no"), f.get("date"), f.get("start"), f.get("end"))


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    return _apply("cancel", logic.cancel, request.form.get("booking_id"))


@bp.route("/day")
@login_required
def day():
    text = request.args.get("date", "").strip()
    try:
        date = logic.parse_date(text)
    except logic.InputError as e:
        return render_template("showrooms/day.html", rooms=[], table={}, date=text, error=str(e)), 400
    rooms = logic.list_rooms()
    table = {r.code: [b for b in logic.list_bookings(date.isoformat()) if b.room == r.code] for r in rooms}
    return render_template("showrooms/day.html", rooms=rooms, table=table, date=text, error=None)


@bp.route("/status.json")
@login_required
def status():
    return jsonify({"bookings": [vars(b) for b in logic.status_bookings()]})

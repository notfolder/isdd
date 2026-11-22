"""研修室の予約。部屋の登録と、60 分単位の予約・取消。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.seminar_rooms import logic

TITLE = "研修室の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS seminar_rooms_room (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS seminar_rooms_booking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES seminar_rooms_room (code),
    employee_no TEXT NOT NULL REFERENCES employees (employee_no),
    date TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

bp = Blueprint("seminar_rooms", __name__, url_prefix="/seminar_rooms", template_folder="templates")


def _render_index(error=None, status=200):
    date_text = request.values.get("date", "").strip()
    day = None
    if date_text:
        try:
            day = logic.parse_date(date_text).isoformat()
        except logic.InputError as exc:
            if error is None:
                error, status = str(exc), 400
    return (
        render_template(
            "seminar_rooms/index.html",
            title=TITLE,
            rooms=logic.list_rooms(),
            bookings=logic.list_bookings(day),
            date=date_text,
            error=error,
        ),
        status,
    )


def _change(action, target_of, run):
    """データを変える操作の共通の流れ。成功すれば記録して一覧へ、だめなら 400。"""
    try:
        result = run()
    except logic.InputError as exc:
        get_db().rollback()
        return _render_index(str(exc), 400)
    audit.record("seminar_rooms", action, target_of(result))
    get_db().commit()
    return redirect(url_for("seminar_rooms.index"))


@bp.route("/")
@login_required
def index():
    return _render_index()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_new():
    form = request.form
    return _change("room_create", lambda r: r.code, lambda: logic.create_room(form.get("code"), form.get("name")))


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_edit():
    form = request.form
    return _change("room_update", lambda r: r.code, lambda: logic.update_room(form.get("code"), form.get("name")))


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    f = request.form
    return _change(
        "book",
        lambda b: str(b.id),
        lambda: logic.create_booking(f.get("room_code"), f.get("employee_no"), f.get("date"), f.get("start"), f.get("end")),
    )


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    return _change("cancel", lambda b: str(b.id), lambda: logic.cancel_booking(request.form.get("booking_id")))


@bp.route("/day")
@login_required
def day():
    date_text = request.args.get("date", "").strip()
    error, status, bookings = None, 200, []
    try:
        bookings = logic.list_bookings(logic.parse_date(date_text).isoformat())
    except logic.InputError as exc:
        error, status = str(exc), 400
    rooms = logic.list_rooms()
    table = [{"room": r, "bookings": [b for b in bookings if b.room_code == r.code]} for r in rooms]
    return render_template("seminar_rooms/day.html", title=TITLE, date=date_text, table=table, error=error), status


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(
        {
            "bookings": [
                {"id": b.id, "room": b.room_code, "employee": b.employee_no, "date": b.date, "start": b.start, "end": b.end}
                for b in logic.list_bookings_by_id()
            ]
        }
    )

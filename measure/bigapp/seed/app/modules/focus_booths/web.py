"""集中ブース予約の画面。判定は domain.py に任せ、例外を 400 に変える。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.focus_booths import domain

bp = Blueprint("focus_booths", __name__, url_prefix="/focus_booths", template_folder="templates")


def _index(error=None, status=200):
    date_text = request.args.get("date", "").strip() or None
    if date_text:
        try:
            domain.parse_date(date_text)
        except domain.BookingError as exc:
            error, status = error or str(exc), 400
            date_text = None
    html = render_template(
        "focus_booths/index.html",
        rooms=domain.list_rooms(),
        bookings=domain.list_bookings(date_text),
        date=date_text or "",
        error=error,
    )
    return html, status


def _act(action, func, *args):
    """判定を呼び、成功なら記録して一覧へ、失敗なら 400 で一覧を返す。"""
    try:
        target = func(*args)
    except domain.BookingError as exc:
        return _index(str(exc), 400)
    audit.record("focus_booths", action, str(target))
    get_db().commit()
    return redirect(url_for("focus_booths.index"))


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_new():
    return _act("room_create", domain.create_room, request.form.get("code"), request.form.get("name"))


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_edit():
    return _act("room_update", domain.update_room, request.form.get("code"), request.form.get("name"))


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    f = request.form
    return _act("book", domain.create_booking, f.get("room_code"), f.get("employee_no"), f.get("date"), f.get("start"), f.get("end"))


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    return _act("cancel", domain.cancel_booking, request.form.get("booking_id"))


@bp.route("/day")
@login_required
def day():
    date_text = request.args.get("date", "").strip()
    error = None
    try:
        domain.parse_date(date_text)
    except domain.BookingError as exc:
        error = str(exc)
    rooms = domain.list_rooms()
    bookings = [] if error else domain.list_bookings(date_text)
    html = render_template("focus_booths/day.html", rooms=rooms, bookings=bookings, date=date_text, error=error)
    return html, (400 if error else 200)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(
        {
            "bookings": [
                {"id": b["id"], "room": b["room_code"], "employee": b["employee_no"], "date": b["date"], "start": b["start"], "end": b["end"]}
                for b in domain.list_bookings()
            ]
        }
    )

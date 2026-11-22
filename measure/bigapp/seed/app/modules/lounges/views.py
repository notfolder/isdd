"""ラウンジ予約の画面と操作。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.lounges import bp
from app.modules.lounges.models import BookingError, LoungeRules, parse_date


def _render(template, error=None, status=200, **extra):
    rules = LoungeRules()
    return render_template(template, rooms=rules.rooms(), error=error, **extra), status


def _index(error=None, status=200):
    date_text = request.values.get("date", "").strip()
    rules = LoungeRules()
    shown_date = ""
    if date_text:
        try:
            shown_date = parse_date(date_text).isoformat()
        except BookingError as e:
            error, status = error or str(e), 400
    return render_template(
        "lounges/index.html", rooms=rules.rooms(), bookings=rules.bookings(shown_date or None), error=error, date=shown_date
    ), status


def _form(name):
    return request.form.get(name, "").strip()


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    code, name = _form("code"), _form("name")
    try:
        LoungeRules().check_new_room(code, name)
    except BookingError as e:
        return _index(str(e), 400)
    conn = get_db()
    conn.execute("INSERT INTO lounges_rooms (code, name) VALUES (?, ?)", (code, name))
    audit.record("lounges", "room_create", code)
    conn.commit()
    return redirect(url_for("lounges.index"))


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    code, name = _form("code"), _form("name")
    try:
        LoungeRules().check_room_update(code, name)
    except BookingError as e:
        return _index(str(e), 400)
    conn = get_db()
    conn.execute("UPDATE lounges_rooms SET name = ? WHERE code = ?", (name, code))
    audit.record("lounges", "room_update", code)
    conn.commit()
    return redirect(url_for("lounges.index"))


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    room_code, employee_no = _form("room_code"), _form("employee_no")
    try:
        date, start, end = LoungeRules().check_booking(room_code, employee_no, _form("date"), _form("start"), _form("end"))
    except BookingError as e:
        return _index(str(e), 400)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO lounges_bookings (room_code, employee_no, date, start, end) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, date, start, end),
    )
    audit.record("lounges", "book", str(cur.lastrowid))
    conn.commit()
    return redirect(url_for("lounges.index"))


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    booking = LoungeRules().active_booking(_form("booking_id"))
    if booking is None:
        return _index("予約が見つかりません", 400)
    conn = get_db()
    conn.execute("UPDATE lounges_bookings SET cancelled = 1 WHERE id = ?", (booking["id"],))
    audit.record("lounges", "cancel", str(booking["id"]))
    conn.commit()
    return redirect(url_for("lounges.index"))


@bp.route("/day")
@login_required
def day():
    rules = LoungeRules()
    try:
        date = parse_date(request.args.get("date", "")).isoformat()
    except BookingError as e:
        return _render("lounges/day.html", str(e), 400, date="", bookings=[])
    return _render("lounges/day.html", date=date, bookings=rules.bookings(date))


@bp.route("/status.json")
@login_required
def status():
    rows = LoungeRules().db.execute("SELECT * FROM lounges_bookings WHERE cancelled = 0 ORDER BY id").fetchall()
    return jsonify(
        {
            "bookings": [
                {"id": r["id"], "room": r["room_code"], "employee": r["employee_no"], "date": r["date"], "start": r["start"], "end": r["end"]}
                for r in rows
            ]
        }
    )

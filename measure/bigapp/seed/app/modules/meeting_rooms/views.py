"""会議室予約の画面と操作。"""

from flask import jsonify, redirect, render_template, request

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db

from . import bp
from .models import BookingRules, format_minute, parse_date, parse_time


def _rooms():
    return get_db().execute("SELECT code, name FROM meeting_rooms_rooms ORDER BY code").fetchall()


def _bookings(date=None):
    sql = (
        "SELECT b.id, b.room_code, b.employee_no, e.name AS employee_name, b.date, b.start_min, b.end_min "
        "FROM meeting_rooms_bookings b LEFT JOIN employees e ON e.employee_no = b.employee_no "
        "WHERE b.cancelled = 0"
    )
    args = []
    if date:
        sql += " AND b.date = ?"
        args.append(date)
    sql += " ORDER BY b.date, b.room_code, b.start_min, b.id"
    rows = get_db().execute(sql, args).fetchall()
    return [dict(r, start=format_minute(r["start_min"]), end=format_minute(r["end_min"])) for r in rows]


def _index(error=None, status=200, date=""):
    return render_template("meeting_rooms/index.html", rooms=_rooms(), bookings=_bookings(date or None), error=error, date=date), status


@bp.route("/")
@login_required
def index():
    date = request.args.get("date", "").strip()
    if date and parse_date(date) is None:
        return _index("日付は YYYY-MM-DD で入力してください", 400)
    return _index(date=date)


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    conn = get_db()
    error = BookingRules(conn).check_room_code(code, name)
    if error is None and conn.execute("SELECT 1 FROM meeting_rooms_rooms WHERE code = ?", (code,)).fetchone():
        error = "この部屋の番号は既に登録されています"
    if error:
        return _index(error, 400)
    conn.execute("INSERT INTO meeting_rooms_rooms (code, name) VALUES (?, ?)", (code, name))
    audit.record("meeting_rooms", "room_create", code)
    conn.commit()
    return redirect("/meeting_rooms/")


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    conn = get_db()
    error = BookingRules(conn).check_room_code(code, name)
    if error is None and conn.execute("SELECT 1 FROM meeting_rooms_rooms WHERE code = ?", (code,)).fetchone() is None:
        error = "部屋が見つかりません"
    if error:
        return _index(error, 400)
    conn.execute("UPDATE meeting_rooms_rooms SET name = ? WHERE code = ?", (name, code))
    audit.record("meeting_rooms", "room_update", code)
    conn.commit()
    return redirect("/meeting_rooms/")


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    form = request.form
    room_code = form.get("room_code", "").strip()
    employee_no = form.get("employee_no", "").strip()
    date, start, end = form.get("date", "").strip(), form.get("start", "").strip(), form.get("end", "").strip()
    conn = get_db()
    error = BookingRules(conn).check_booking(room_code, employee_no, date, start, end)
    if error:
        return _index(error, 400)
    cur = conn.execute(
        "INSERT INTO meeting_rooms_bookings (room_code, employee_no, date, start_min, end_min) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, date, parse_time(start), parse_time(end)),
    )
    audit.record("meeting_rooms", "book", str(cur.lastrowid))
    conn.commit()
    return redirect("/meeting_rooms/")


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    raw = request.form.get("booking_id", "").strip()
    conn = get_db()
    row = conn.execute("SELECT * FROM meeting_rooms_bookings WHERE id = ?", (int(raw),)).fetchone() if raw.isdigit() else None
    if row is None:
        return _index("予約が見つかりません", 400)
    if row["cancelled"]:
        return _index("この予約は既に取り消されています", 400)
    conn.execute("UPDATE meeting_rooms_bookings SET cancelled = 1 WHERE id = ?", (row["id"],))
    audit.record("meeting_rooms", "cancel", str(row["id"]))
    conn.commit()
    return redirect("/meeting_rooms/")


@bp.route("/day")
@login_required
def day():
    date = request.args.get("date", "").strip()
    if parse_date(date) is None:
        return render_template("meeting_rooms/day.html", rooms=_rooms(), bookings=[], date=date, error="日付は YYYY-MM-DD で入力してください"), 400
    bookings = _bookings(date)
    by_room = {r["code"]: [b for b in bookings if b["room_code"] == r["code"]] for r in _rooms()}
    return render_template("meeting_rooms/day.html", rooms=_rooms(), by_room=by_room, date=date, error=None)


@bp.route("/status.json")
@login_required
def status():
    rows = _bookings()
    rows.sort(key=lambda r: r["id"])
    return jsonify({"bookings": [
        {"id": r["id"], "room": r["room_code"], "employee": r["employee_no"], "date": r["date"], "start": r["start"], "end": r["end"]}
        for r in rows
    ]})

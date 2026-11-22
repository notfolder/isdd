"""応接室の予約の画面。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.reception_rooms import TITLE, bp, queries, rules


def _index_page(error=None, status=200):
    date_text = request.values.get("date", "").strip() if request.method == "GET" else ""
    if date_text and rules.parse_date(date_text) is None:
        error, status, date_text = "日付は YYYY-MM-DD で入力してください", 400, ""
    html = render_template(
        "reception_rooms/index.html",
        title=TITLE,
        rooms=queries.rooms(),
        bookings=queries.bookings(date_text),
        date=date_text,
        error=error,
    )
    return html, status


def _reject(message):
    return _index_page(error=message, status=400)


def _done():
    return redirect(url_for("reception_rooms.index"))


@bp.route("/")
@login_required
def index():
    return _index_page()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_new():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not code:
        return _reject("部屋の番号を入力してください")
    if not name:
        return _reject("部屋の名前を入力してください")
    if queries.find_room(code):
        return _reject("この部屋の番号は既に登録されています")
    queries.add_room(code, name)
    audit.record("reception_rooms", "room_create", code)
    get_db().commit()
    return _done()


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_edit():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not queries.find_room(code):
        return _reject("部屋が見つかりません")
    if not name:
        return _reject("部屋の名前を入力してください")
    queries.rename_room(code, name)
    audit.record("reception_rooms", "room_update", code)
    get_db().commit()
    return _done()


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    form = request.form
    room_code = form.get("room_code", "").strip()
    employee_no = form.get("employee_no", "").strip()
    date = rules.parse_date(form.get("date"))
    start, end = rules.parse_time(form.get("start")), rules.parse_time(form.get("end"))

    if not queries.find_room(room_code):
        return _reject("部屋が見つかりません")
    if not queries.find_active_employee(employee_no):
        return _reject("在籍している社員ではありません")
    if date is None:
        return _reject("日付は YYYY-MM-DD で入力してください")
    if start is None or end is None:
        return _reject("時刻は HH:MM で入力してください")
    error = rules.check_time_range(start, end) or rules.check_not_past(date, clock.today())
    if error:
        return _reject(error)

    date_text, start_text, end_text = date.isoformat(), rules.format_time(start), rules.format_time(end)
    if queries.has_overlap(room_code, date_text, start_text, end_text):
        return _reject("その時間は既に予約されています")
    error = rules.check_daily_limit(queries.count_for_day(employee_no, date_text))
    if error:
        return _reject(error)

    booking_id = queries.add_booking(room_code, employee_no, date_text, start_text, end_text)
    audit.record("reception_rooms", "book", str(booking_id))
    get_db().commit()
    return _done()


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    raw = request.form.get("booking_id", "").strip()
    booking_id = int(raw) if raw.isdigit() else None
    if booking_id is None or not queries.find_booking(booking_id):
        return _reject("予約が見つかりません")
    queries.cancel_booking(booking_id)
    audit.record("reception_rooms", "cancel", str(booking_id))
    get_db().commit()
    return _done()


@bp.route("/day")
@login_required
def day():
    date = rules.parse_date(request.args.get("date"))
    if date is None:
        return render_template("reception_rooms/day.html", title=TITLE, error="日付は YYYY-MM-DD で入力してください", date="", rooms=[], by_room={}), 400
    rows = queries.bookings(date.isoformat())
    by_room = {}
    for row in rows:
        by_room.setdefault(row["room_code"], []).append(row)
    return render_template("reception_rooms/day.html", title=TITLE, error=None, date=date.isoformat(), rooms=queries.rooms(), by_room=by_room)


@bp.route("/status.json")
@login_required
def status():
    return jsonify(
        {
            "bookings": [
                {"id": r["id"], "room": r["room_code"], "employee": r["employee_no"], "date": r["date"], "start": r["start"], "end": r["end"]}
                for r in queries.status_rows()
            ]
        }
    )

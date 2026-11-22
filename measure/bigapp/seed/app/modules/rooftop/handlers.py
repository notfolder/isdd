"""屋上予約の画面。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.rooftop import bp, queries, rules
from app.modules.rooftop.rules import RuleError


def _render_index(error=None, status=200, date=""):
    rows = queries.bookings(date or None)
    return (
        render_template(
            "rooftop/index.html",
            rooms=queries.rooms(),
            bookings=rows,
            date=date,
            error=error,
            fmt=rules.format_minute,
        ),
        status,
    )


def _done(action, target):
    audit.record("rooftop", action, target)
    get_db().commit()
    return redirect(url_for("rooftop.index"))


def _clean(name):
    return request.form.get(name, "").strip()


@bp.route("/")
@login_required
def index():
    date = request.args.get("date", "").strip()
    if date:
        try:
            rules.parse_date(date)
        except RuleError as e:
            return _render_index(str(e), 400)
    return _render_index(date=date)


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    code, name = _clean("code"), _clean("name")
    if not code:
        return _render_index("部屋の番号を入力してください", 400)
    if not name:
        return _render_index("部屋の名前を入力してください", 400)
    if queries.get_room(code):
        return _render_index("この部屋の番号は既に登録されています", 400)
    queries.insert_room(code, name)
    return _done("room_create", code)


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    code, name = _clean("code"), _clean("name")
    if not queries.get_room(code):
        return _render_index("部屋が見つかりません", 400)
    if not name:
        return _render_index("部屋の名前を入力してください", 400)
    queries.update_room(code, name)
    return _done("room_update", code)


def _validate_booking(room_code, employee_no, date_text, start_text, end_text):
    """予約の入力を確かめ、(日付の文字列, 開始, 終了) を返す。受け付けられなければ RuleError。"""
    date = rules.parse_date(date_text)
    start, end = rules.parse_time(start_text), rules.parse_time(end_text)
    rules.check_slot(start, end)
    rules.check_not_past(date, clock.today())
    if not queries.get_room(room_code):
        raise RuleError("部屋が見つかりません")
    employee = queries.get_employee(employee_no)
    if employee is None or not rules.is_eligible(employee["status"]):
        raise RuleError("予約できる社員ではありません")
    day = date.isoformat()
    if any(rules.overlaps(start, end, s["start_min"], s["end_min"]) for s in queries.room_day_slots(room_code, day)):
        raise RuleError("その時間は既に予約されています")
    if queries.person_day_count(employee_no, day) >= rules.MAX_BOOKINGS_PER_DAY:
        raise RuleError("1 人が 1 日に取れる予約は 1 件までです")
    return day, start, end


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    room_code, employee_no = _clean("room_code"), _clean("employee_no")
    try:
        day, start, end = _validate_booking(room_code, employee_no, _clean("date"), _clean("start"), _clean("end"))
    except RuleError as e:
        return _render_index(str(e), 400)
    queries.insert_booking(room_code, employee_no, day, start, end)
    return _done("book", f"{room_code} {employee_no} {day} {rules.format_minute(start)}-{rules.format_minute(end)}")


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    raw = _clean("booking_id")
    row = queries.get_booking(int(raw)) if raw.isdigit() else None
    if row is None or row["cancelled"]:
        return _render_index("取り消せる予約が見つかりません", 400)
    queries.cancel_booking(row["id"])
    return _done("cancel", str(row["id"]))


@bp.route("/day")
@login_required
def day():
    date_text = request.args.get("date", "").strip()
    try:
        date = rules.parse_date(date_text)
    except RuleError as e:
        return _render_index(str(e), 400)
    rows = queries.bookings(date.isoformat())
    by_room = {r["code"]: [b for b in rows if b["room_code"] == r["code"]] for r in queries.rooms()}
    return render_template("rooftop/day.html", date=date.isoformat(), rooms=queries.rooms(), by_room=by_room, fmt=rules.format_minute)


@bp.route("/status.json")
@login_required
def status():
    return jsonify(
        {
            "bookings": [
                {
                    "id": b["id"],
                    "room": b["room_code"],
                    "employee": b["employee_no"],
                    "date": b["date"],
                    "start": rules.format_minute(b["start_min"]),
                    "end": rules.format_minute(b["end_min"]),
                }
                for b in queries.bookings()
            ]
        }
    )

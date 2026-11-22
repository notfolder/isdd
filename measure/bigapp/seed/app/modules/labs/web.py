"""実験室の予約の画面。判定は domain.py に任せ、例外を 400 にして返す。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.labs import bp, domain


def _page(template, error=None, status=200, **extra):
    return render_template(f"labs/{template}", error=error, rooms=domain.list_rooms(), **extra), status


def _index(error=None, status=200):
    date_text = request.values.get("date", "").strip()
    try:
        rows = domain.list_bookings(date_text or None)
    except domain.BookingError as exc:
        rows, error, status = [], error or str(exc), 400
    return _page("index.html", error, status, bookings=rows, date=date_text)


def _change(action, func, target_of):
    """データを変える操作の共通の流れ。成功なら記録して一覧へ、だめなら 400。"""
    try:
        target = func()
    except domain.BookingError as exc:
        get_db().rollback()
        return _index(str(exc), 400)
    audit.record("labs", action, str(target_of(target)))
    get_db().commit()
    return redirect(url_for("labs.index"))


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    f = request.form
    return _change("room_create", lambda: domain.create_room(f.get("code"), f.get("name")), lambda t: t)


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    f = request.form
    return _change("room_update", lambda: domain.update_room(f.get("code"), f.get("name")), lambda t: t)


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    f = request.form
    return _change(
        "book",
        lambda: domain.book(f.get("room_code", "").strip(), f.get("employee_no", "").strip(), f.get("date", "").strip(), f.get("start", "").strip(), f.get("end", "").strip()),
        lambda t: t,
    )


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    return _change("cancel", lambda: domain.cancel(request.form.get("booking_id", "").strip()), lambda t: t)


@bp.route("/day")
@login_required
def day():
    date_text = request.args.get("date", "").strip()
    try:
        rows = domain.list_bookings(date_text)
    except domain.BookingError as exc:
        return _page("day.html", str(exc), 400, bookings=[], date=date_text)
    if not date_text:
        return _page("day.html", "日付を入力してください", 400, bookings=[], date=date_text)
    by_room = {r["code"]: [b for b in rows if b["room_code"] == r["code"]] for r in domain.list_rooms()}
    return _page("day.html", None, 200, by_room=by_room, date=date_text)


@bp.route("/status.json")
@login_required
def status():
    return jsonify(
        {
            "bookings": [
                {"id": b["id"], "room": b["room_code"], "employee": b["employee_no"], "date": b["date"], "start": b["start"], "end": b["end"]}
                for b in domain.list_bookings()
            ]
        }
    )

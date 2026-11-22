"""予約の画面。判定は domain.py に任せ、GymError を受けて 400 で返す。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core import audit
from app.core.auth import login_required, staff_required
from app.core.db import get_db
from app.modules.gym import domain

bp = Blueprint("gym", __name__, url_prefix="/gym", template_folder="templates")


def _page(error=None, status=200, date_text=None):
    try:
        bookings = domain.list_bookings(date_text)
    except domain.GymError as exc:
        bookings, error, status = domain.list_bookings(), error or str(exc), 400
    return render_template(
        "gym/index.html", rooms=domain.list_rooms(), bookings=bookings, error=error, date=date_text or ""
    ), status


def _change(action, func, target_of, *args):
    """データを変える操作の共通の流れ。成功なら記録して一覧へ、失敗なら 400。"""
    conn = get_db()
    try:
        target = target_of(func(*args))
    except domain.GymError as exc:
        conn.rollback()
        return _page(str(exc), 400)
    audit.record("gym", action, target)
    conn.commit()
    return redirect(url_for("gym.index"))


@bp.route("/")
@login_required
def index():
    return _page(date_text=request.args.get("date") or None)


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    f = request.form
    return _change("room_create", domain.create_room, str, f.get("code"), f.get("name"))


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    f = request.form
    return _change("room_update", domain.update_room, str, f.get("code"), f.get("name"))


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    f = request.form
    return _change(
        "book", domain.book, str, f.get("room_code"), f.get("employee_no"), f.get("date"), f.get("start"), f.get("end")
    )


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    return _change("cancel", domain.cancel, str, request.form.get("booking_id"))


@bp.route("/day")
@login_required
def day():
    try:
        date_text = request.args.get("date", "")
        domain.parse_date(date_text)
        rows = domain.list_bookings(date_text)
    except domain.GymError as exc:
        return render_template("gym/day.html", error=str(exc), date=request.args.get("date", ""), rooms=[]), 400
    by_room = {r["code"]: [] for r in domain.list_rooms()}
    for b in rows:
        by_room[b["room"]].append(b)
    rooms = [{"code": r["code"], "name": r["name"], "bookings": by_room[r["code"]]} for r in domain.list_rooms()]
    return render_template("gym/day.html", error=None, date=date_text, rooms=rooms)


@bp.route("/status.json")
@login_required
def status_json():
    items = [
        {k: b[k] for k in ("id", "room", "employee", "date", "start", "end")} for b in domain.list_bookings()
    ]
    return jsonify({"bookings": items})

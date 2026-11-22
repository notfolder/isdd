"""Web 会議ブースの画面。判定は service.py、SQL は repo.py。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core.auth import login_required, staff_required
from app.modules.web_booths import repo, service
from app.modules.web_booths.service import BookingError

bp = Blueprint("web_booths", __name__, url_prefix="/web_booths", template_folder="templates")


def _index(error=None, status=200, date=None):
    return (
        render_template(
            "web_booths/index.html",
            rooms=repo.list_rooms(),
            bookings=repo.list_bookings(date),
            date=date or "",
            error=error,
        ),
        status,
    )


def _act(func, *args):
    """操作を実行する。受け付けなければ 400 で理由を出し、成功なら一覧へ戻す。"""
    try:
        func(*args)
    except BookingError as e:
        return _index(error=str(e), status=400)
    return redirect(url_for("web_booths.index"))


@bp.route("/")
@login_required
def index():
    try:
        date = service.check_date_filter(request.args.get("date", "").strip())
    except BookingError as e:
        return _index(error=str(e), status=400)
    return _index(date=date)


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_new():
    return _act(service.create_room, request.form.get("code"), request.form.get("name"))


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_edit():
    return _act(service.update_room, request.form.get("code"), request.form.get("name"))


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    f = request.form
    return _act(service.book, f.get("room_code"), f.get("employee_no"), f.get("date"), f.get("start"), f.get("end"))


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    return _act(service.cancel, request.form.get("booking_id"))


@bp.route("/day")
@login_required
def day():
    try:
        date = service.check_date_filter(request.args.get("date", "").strip()) or ""
        if not date:
            raise BookingError("日付を指定してください")
    except BookingError as e:
        return render_template("web_booths/day.html", rooms=[], table={}, date="", error=str(e)), 400
    rooms = repo.list_rooms()
    table = {r["code"]: [] for r in rooms}
    for b in repo.list_bookings(date):
        table.setdefault(b["room_code"], []).append(b)
    return render_template("web_booths/day.html", rooms=rooms, table=table, date=date, error=None)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(service.status())

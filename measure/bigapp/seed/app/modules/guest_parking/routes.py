"""来客用駐車場の画面。"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core.auth import login_required, staff_required
from app.modules.guest_parking import service
from app.modules.guest_parking.service import InputError

bp = Blueprint("guest_parking", __name__, url_prefix="/guest_parking", template_folder="templates")


def _index(error=None, status=200):
    date_text = request.args.get("date", "")
    try:
        rooms, bookings = service.list_view(date_text)
    except InputError as e:
        rooms, bookings = service.list_view(""), []
        error, status = error or str(e), 400
    return render_template("guest_parking/index.html", rooms=rooms, bookings=bookings, error=error, date=date_text), status


@bp.route("/")
@login_required
def index():
    return _index()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_new():
    try:
        service.create_room(request.form.get("code"), request.form.get("name"))
    except InputError as e:
        return _index(str(e), 400)
    return redirect(url_for("guest_parking.index"))


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_edit():
    try:
        service.update_room(request.form.get("code"), request.form.get("name"))
    except InputError as e:
        return _index(str(e), 400)
    return redirect(url_for("guest_parking.index"))


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    f = request.form
    try:
        service.book(f.get("room_code"), f.get("employee_no"), f.get("date"), f.get("start"), f.get("end"))
    except InputError as e:
        return _index(str(e), 400)
    return redirect(url_for("guest_parking.index"))


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    try:
        service.cancel(request.form.get("booking_id"))
    except InputError as e:
        return _index(str(e), 400)
    return redirect(url_for("guest_parking.index"))


@bp.route("/day")
@login_required
def day():
    date_text = request.args.get("date", "")
    try:
        table = service.day_table(date_text)
    except InputError as e:
        return render_template("guest_parking/day.html", table=[], date=date_text, error=str(e)), 400
    return render_template("guest_parking/day.html", table=table, date=date_text, error=None)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(service.status())

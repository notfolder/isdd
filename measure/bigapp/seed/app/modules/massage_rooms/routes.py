"""画面の層。入出力だけを扱い、判定は service に任せる。"""

from flask import jsonify, redirect, render_template, request, url_for

from app.core.auth import login_required, staff_required

from . import bp, service


def _index(error=None, status=200):
    date = request.values.get("date", "") if request.method == "GET" else ""
    try:
        rows = service.bookings(date or None)
    except service.RuleError as exc:
        rows, error, status = service.bookings(), error or str(exc), 400
    page = render_template(
        "massage_rooms/index.html", rooms=service.rooms(), bookings=rows, date=date, error=error, settings=service.SETTINGS
    )
    return page, status


def _act(action, *args):
    """操作を実行し、成功なら一覧へ、きまりに合わなければ 400 で理由を出す。"""
    try:
        action(*args)
    except service.RuleError as exc:
        return _index(error=str(exc), status=400)
    return redirect(url_for("massage_rooms.index"))


@bp.route("/")
@login_required
def index():
    return _index()


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
        date, table = service.day_table(request.args.get("date"))
    except service.RuleError as exc:
        return render_template("massage_rooms/day.html", date="", table=[], error=str(exc)), 400
    return render_template("massage_rooms/day.html", date=date, table=table, error=None)


@bp.route("/status.json")
@login_required
def status():
    return jsonify({"bookings": service.bookings()})

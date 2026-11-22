"""社用バスの予約。部屋（便）を登録し、30 分単位で予約する（総務規程 第 4 条・第 6 条・第 7 条）。"""

import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db

bp = Blueprint("shuttle", __name__, url_prefix="/shuttle", template_folder="templates")
TITLE = "社用バスの予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS shuttle_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shuttle_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES shuttle_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

# 取れる開始時刻の一覧（9:00 から 17:30 まで 30 分刻み）。終了時刻は 9:30 から 18:00 まで。
ALLOWED_STARTS = tuple(f"{h:02d}:{m:02d}" for h in range(9, 18) for m in (0, 30))
ALLOWED_ENDS = ALLOWED_STARTS[1:] + ("18:00",)
MAX_PER_DAY = 2


def _rooms():
    return get_db().execute("SELECT code, name FROM shuttle_rooms ORDER BY code").fetchall()


def _bookings(date=None):
    """取り消していない予約。date があればその日だけ。"""
    sql = (
        "SELECT b.id, b.room_code, b.employee_no, b.date, b.start, b.end, e.name AS employee_name "
        "FROM shuttle_bookings b LEFT JOIN employees e ON e.employee_no = b.employee_no WHERE b.cancelled = 0"
    )
    args = []
    if date:
        sql += " AND b.date = ?"
        args.append(date)
    return get_db().execute(sql + " ORDER BY b.date, b.room_code, b.start, b.id", args).fetchall()


def _parse_date(text):
    """YYYY-MM-DD を日付にする。形式が違えば None。"""
    try:
        if len(text) != 10:
            return None
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


def _page(error=None, status=200):
    """一覧の画面。error があれば理由を出して返す。"""
    date = request.args.get("date", "").strip() or None
    html = render_template(
        "shuttle/index.html", rooms=_rooms(), bookings=_bookings(date), error=error, date=date or "",
        starts=ALLOWED_STARTS, ends=ALLOWED_ENDS,
    )
    return html, status


def _done():
    get_db().commit()
    return redirect(url_for("shuttle.index"))


@bp.route("/")
@login_required
def index():
    return _page()


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    if not code:
        return _page("部屋の番号を入力してください", 400)
    if not name:
        return _page("名前を入力してください", 400)
    conn = get_db()
    if conn.execute("SELECT 1 FROM shuttle_rooms WHERE code = ?", (code,)).fetchone():
        return _page("この部屋の番号は既に登録されています", 400)
    conn.execute("INSERT INTO shuttle_rooms (code, name) VALUES (?, ?)", (code, name))
    audit.record("shuttle", "room_create", code)
    return _done()


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    code, name = request.form.get("code", "").strip(), request.form.get("name", "").strip()
    conn = get_db()
    if not conn.execute("SELECT 1 FROM shuttle_rooms WHERE code = ?", (code,)).fetchone():
        return _page("部屋が見つかりません", 400)
    if not name:
        return _page("名前を入力してください", 400)
    conn.execute("UPDATE shuttle_rooms SET name = ? WHERE code = ?", (name, code))
    audit.record("shuttle", "room_update", code)
    return _done()


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    form = request.form
    room, number = form.get("room_code", "").strip(), form.get("employee_no", "").strip()
    date_text, start, end = form.get("date", "").strip(), form.get("start", "").strip(), form.get("end", "").strip()
    conn = get_db()
    if not conn.execute("SELECT 1 FROM shuttle_rooms WHERE code = ?", (room,)).fetchone():
        return _page("部屋が見つかりません", 400)
    # 在籍している社員だけが対象（総務規程 第 6 条）
    if not conn.execute("SELECT 1 FROM employees WHERE employee_no = ? AND status <> 'retired'", (number,)).fetchone():
        return _page("在籍している社員ではありません", 400)
    date = _parse_date(date_text)
    if date is None:
        return _page("日付は YYYY-MM-DD で入力してください", 400)
    if date < clock.today():
        return _page("過去の日付は予約できません", 400)
    if start not in ALLOWED_STARTS or end not in ALLOWED_ENDS:
        return _page("時刻は 9:00 から 18:00 の間の 30 分単位で入力してください", 400)
    if start >= end:
        return _page("開始は終了より前にしてください", 400)
    # 時間が重なる予約（終了と開始が同じ時刻は重ならない）
    if conn.execute(
        "SELECT 1 FROM shuttle_bookings WHERE room_code = ? AND date = ? AND cancelled = 0 AND start < ? AND end > ?",
        (room, date_text, end, start),
    ).fetchone():
        return _page("その時間は既に予約されています", 400)
    count = conn.execute(
        "SELECT COUNT(*) FROM shuttle_bookings WHERE employee_no = ? AND date = ? AND cancelled = 0", (number, date_text)
    ).fetchone()[0]
    if count >= MAX_PER_DAY:
        return _page("1 人が 1 日に取れる予約は 2 件までです", 400)
    cur = conn.execute(
        "INSERT INTO shuttle_bookings (room_code, employee_no, date, start, end) VALUES (?, ?, ?, ?, ?)",
        (room, number, date_text, start, end),
    )
    audit.record("shuttle", "book", str(cur.lastrowid))
    return _done()


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    booking_id = request.form.get("booking_id", "").strip()
    conn = get_db()
    row = conn.execute("SELECT id FROM shuttle_bookings WHERE id = ? AND cancelled = 0", (booking_id,)).fetchone() if booking_id.isdigit() else None
    if row is None:
        return _page("予約が見つかりません", 400)
    conn.execute("UPDATE shuttle_bookings SET cancelled = 1 WHERE id = ?", (row["id"],))
    audit.record("shuttle", "cancel", str(row["id"]))
    return _done()


@bp.route("/day")
@login_required
def day():
    date = request.args.get("date", "").strip()
    if _parse_date(date) is None:
        return render_template("shuttle/day.html", date=date, rooms=[], bookings={}, error="日付は YYYY-MM-DD で入力してください"), 400
    grouped = {}
    for b in _bookings(date):
        grouped.setdefault(b["room_code"], []).append(b)
    return render_template("shuttle/day.html", date=date, rooms=_rooms(), bookings=grouped, error=None)


@bp.route("/status.json")
@login_required
def status_json():
    rows = _bookings()
    rows = sorted(rows, key=lambda r: r["id"])
    return jsonify({"bookings": [
        {"id": r["id"], "room": r["room_code"], "employee": r["employee_no"], "date": r["date"], "start": r["start"], "end": r["end"]}
        for r in rows
    ]})

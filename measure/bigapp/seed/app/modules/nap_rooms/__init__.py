"""仮眠室の予約。部屋を登録し、在籍している社員の予約を 30 分単位で受け付ける。"""

import datetime
import re

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db

bp = Blueprint("nap_rooms", __name__, url_prefix="/nap_rooms", template_folder="templates")
TITLE = "仮眠室の予約"

SCHEMA = """
CREATE TABLE IF NOT EXISTS nap_rooms_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nap_rooms_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES nap_rooms_rooms(code),
    employee_no TEXT NOT NULL,
    book_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""

# 予約の開始・終了に使える時刻（9:00 から 18:00 まで 30 分刻み）。
ALLOWED_STARTS = tuple(f"{h:02d}:{m:02d}" for h in range(9, 18) for m in (0, 30)) + ("18:00",)
TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(text):
    """YYYY-MM-DD の日付を読む。形式が違えば ValueError。"""
    text = (text or "").strip()
    if not DATE_PATTERN.match(text):
        raise ValueError("日付は YYYY-MM-DD の形式で入力してください")
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise ValueError("日付が正しくありません")


def _rooms():
    return get_db().execute("SELECT code, name FROM nap_rooms_rooms ORDER BY code").fetchall()


def _bookings(date_text=None):
    sql = (
        "SELECT b.id, b.room_code, b.employee_no, e.name AS employee_name, b.book_date, b.start_time, b.end_time "
        "FROM nap_rooms_bookings b LEFT JOIN employees e ON e.employee_no = b.employee_no "
        "WHERE b.cancelled = 0"
    )
    args = []
    if date_text:
        sql += " AND b.book_date = ?"
        args.append(date_text)
    sql += " ORDER BY b.book_date, b.room_code, b.start_time, b.id"
    return get_db().execute(sql, args).fetchall()


def _render_index(error=None, status=200, date_text=""):
    return render_template(
        "nap_rooms/index.html", rooms=_rooms(), bookings=_bookings(date_text or None), error=error, date=date_text
    ), status


def _fail(error):
    return _render_index(error=error, status=400)


@bp.route("/")
@login_required
def index():
    date_text = request.args.get("date", "").strip()
    if date_text:
        try:
            _parse_date(date_text)
        except ValueError as e:
            return _fail(str(e))
    return _render_index(date_text=date_text)


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    if not code:
        return _fail("部屋の番号を入力してください")
    if not name:
        return _fail("部屋の名前を入力してください")
    conn = get_db()
    if conn.execute("SELECT 1 FROM nap_rooms_rooms WHERE code = ?", (code,)).fetchone():
        return _fail("この部屋の番号は既に登録されています")
    conn.execute("INSERT INTO nap_rooms_rooms (code, name) VALUES (?, ?)", (code, name))
    audit.record("nap_rooms", "room_create", code)
    conn.commit()
    return redirect("/nap_rooms/")


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    conn = get_db()
    if conn.execute("SELECT 1 FROM nap_rooms_rooms WHERE code = ?", (code,)).fetchone() is None:
        return _fail("部屋が見つかりません")
    if not name:
        return _fail("部屋の名前を入力してください")
    conn.execute("UPDATE nap_rooms_rooms SET name = ? WHERE code = ?", (name, code))
    audit.record("nap_rooms", "room_update", code)
    conn.commit()
    return redirect("/nap_rooms/")


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    form = request.form
    room_code = form.get("room_code", "").strip()
    employee_no = form.get("employee_no", "").strip()
    start = form.get("start", "").strip()
    end = form.get("end", "").strip()
    conn = get_db()
    try:
        day = _parse_date(form.get("date"))
        if conn.execute("SELECT 1 FROM nap_rooms_rooms WHERE code = ?", (room_code,)).fetchone() is None:
            raise ValueError("部屋が見つかりません")
        # 在籍している社員だけを対象にする（退職者・存在しない社員番号は読めない）。
        employee = conn.execute(
            "SELECT employee_no FROM employees WHERE employee_no = ? AND status <> 'retired'", (employee_no,)
        ).fetchone()
        if employee is None:
            raise ValueError("在籍している社員が見つかりません")
        if not (TIME_PATTERN.match(start) and TIME_PATTERN.match(end)):
            raise ValueError("時刻は HH:MM の形式で入力してください")
        if start not in ALLOWED_STARTS or end not in ALLOWED_STARTS:
            raise ValueError("時刻は 9:00 から 18:00 の間の 30 分単位で入力してください")
        if start >= end:
            raise ValueError("開始は終了より前の時刻にしてください")
        if day < clock.today():
            raise ValueError("過去の日付は予約できません")
        date_text = day.isoformat()
        if conn.execute(
            "SELECT 1 FROM nap_rooms_bookings WHERE employee_no = ? AND book_date = ? AND cancelled = 0",
            (employee_no, date_text),
        ).fetchone():
            raise ValueError("この社員は同じ日に既に予約しています")
        # 重なり: 既存の開始 < 新しい終了 かつ 新しい開始 < 既存の終了（端が接するだけなら重ならない）。
        if conn.execute(
            "SELECT 1 FROM nap_rooms_bookings WHERE room_code = ? AND book_date = ? AND cancelled = 0 "
            "AND start_time < ? AND ? < end_time",
            (room_code, date_text, end, start),
        ).fetchone():
            raise ValueError("その時間はすでに予約があります")
    except ValueError as e:
        return _fail(str(e))
    cur = conn.execute(
        "INSERT INTO nap_rooms_bookings (room_code, employee_no, book_date, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, date_text, start, end),
    )
    audit.record("nap_rooms", "book", str(cur.lastrowid))
    conn.commit()
    return redirect("/nap_rooms/")


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    booking_id = request.form.get("booking_id", "").strip()
    conn = get_db()
    row = None
    if booking_id.isdigit():
        row = conn.execute("SELECT id FROM nap_rooms_bookings WHERE id = ? AND cancelled = 0", (int(booking_id),)).fetchone()
    if row is None:
        return _fail("取り消せる予約が見つかりません")
    conn.execute("UPDATE nap_rooms_bookings SET cancelled = 1 WHERE id = ?", (row["id"],))
    audit.record("nap_rooms", "cancel", str(row["id"]))
    conn.commit()
    return redirect("/nap_rooms/")


@bp.route("/day")
@login_required
def day():
    date_text = request.args.get("date", "").strip()
    try:
        _parse_date(date_text)
    except ValueError as e:
        return _fail(str(e))
    rooms = _rooms()
    bookings = _bookings(date_text)
    by_room = {r["code"]: [b for b in bookings if b["room_code"] == r["code"]] for r in rooms}
    return render_template("nap_rooms/day.html", rooms=rooms, by_room=by_room, date=date_text)


@bp.route("/status.json")
@login_required
def status_json():
    rows = get_db().execute(
        "SELECT id, room_code, employee_no, book_date, start_time, end_time FROM nap_rooms_bookings "
        "WHERE cancelled = 0 ORDER BY id"
    ).fetchall()
    return jsonify(
        {
            "bookings": [
                {"id": r["id"], "room": r["room_code"], "employee": r["employee_no"], "date": r["book_date"],
                 "start": r["start_time"], "end": r["end_time"]}
                for r in rows
            ]
        }
    )

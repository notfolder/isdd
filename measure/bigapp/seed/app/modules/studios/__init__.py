"""撮影スタジオの予約（総務規程 第 4・6・7 条）。

部屋を登録し、社員が日付と時間を指定して予約する。すべてこのファイルに関数で書く。
"""

import datetime

from flask import Blueprint, jsonify, redirect, render_template, request

from app.core import audit, clock
from app.core.auth import login_required, staff_required
from app.core.db import get_db

bp = Blueprint("studios", __name__, url_prefix="/studios", template_folder="templates")
TITLE = "撮影スタジオの予約"

# 機能の設定。時間は分で持つ。
SETTINGS = {
    "unit_minutes": 60,  # 予約の時間の単位
    "open_minutes": 9 * 60,  # 利用できる最初の時刻（9:00）
    "close_minutes": 18 * 60,  # 利用できる最後の時刻（18:00）
    "per_day_limit": 1,  # 1 人が同じ日に取れる予約の数
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS studios_rooms (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS studios_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL REFERENCES studios_rooms(code),
    employee_no TEXT NOT NULL,
    date TEXT NOT NULL,
    start_min INTEGER NOT NULL,
    end_min INTEGER NOT NULL,
    cancelled INTEGER NOT NULL DEFAULT 0
);
"""


def parse_date(text):
    """YYYY-MM-DD の文字列を日付にする。形式が違えば None。"""
    text = (text or "").strip()
    if len(text) != 10:
        return None
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


def parse_time(text):
    """HH:MM の文字列を 0 時からの分にする。形式が違えば None。"""
    text = (text or "").strip()
    parts = text.split(":")
    if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 2:
        return None
    if not (parts[0].isdigit() and parts[1].isdigit()):
        return None
    hour, minute = int(parts[0]), int(parts[1])
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def format_time(minutes):
    """0 時からの分を HH:MM にする。"""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def list_rooms():
    return get_db().execute("SELECT code, name FROM studios_rooms ORDER BY code").fetchall()


def list_bookings(date_text=None, room_code=None):
    """取り消していない予約を id の昇順で返す。"""
    sql = (
        "SELECT b.id, b.room_code, b.employee_no, b.date, b.start_min, b.end_min, e.name AS employee_name "
        "FROM studios_bookings b LEFT JOIN employees e ON e.employee_no = b.employee_no "
        "WHERE b.cancelled = 0"
    )
    args = []
    if date_text:
        sql += " AND b.date = ?"
        args.append(date_text)
    if room_code:
        sql += " AND b.room_code = ?"
        args.append(room_code)
    return get_db().execute(sql + " ORDER BY b.id", args).fetchall()


def render_index(error=None, status=200, date_text=""):
    rows = list_bookings(date_text if parse_date(date_text) else None)
    return (
        render_template(
            "studios/index.html",
            rooms=list_rooms(),
            bookings=rows,
            error=error,
            date=date_text,
            format_time=format_time,
        ),
        status,
    )


def render_day(date_text, error=None, status=200):
    day = parse_date(date_text)
    rooms = list_rooms()
    table = []
    if day:
        for room in rooms:
            table.append({"room": room, "bookings": list_bookings(day.isoformat(), room["code"])})
    return (
        render_template("studios/day.html", table=table, date=date_text, error=error, format_time=format_time),
        status,
    )


def check_room_input(code, name):
    """部屋の入力の誤りを文章で返す。問題なければ None。"""
    if not code:
        return "部屋の番号を入力してください"
    if not name:
        return "部屋の名前を入力してください"
    return None


def check_booking(room_code, employee_no, day, start, end):
    """予約の入力を総務規程に照らして確かめる。受け付けられない理由を返す。問題なければ None。"""
    db = get_db()
    if db.execute("SELECT 1 FROM studios_rooms WHERE code = ?", (room_code,)).fetchone() is None:
        return "部屋が見つかりません"
    # 在籍の判定: 退職していない社員だけが対象（存在しない社員番号は行が無いので対象外）
    employee = db.execute("SELECT status FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if employee is None:
        return "社員が見つかりません"
    if employee["status"] == "retired":
        return "退職した社員は予約できません"
    if day is None:
        return "日付は YYYY-MM-DD の形で入力してください"
    if start is None or end is None:
        return "時刻は HH:MM の形で入力してください"
    unit = SETTINGS["unit_minutes"]
    if start % unit != 0 or end % unit != 0:
        return f"予約は {unit} 分の単位です"
    if start < SETTINGS["open_minutes"] or end > SETTINGS["close_minutes"]:
        return "予約できる時間は 9:00 から 18:00 の間です"
    if start >= end:
        return "終了は開始より後にしてください"
    if day < clock.today():
        return "過去の日付は予約できません"
    date_text = day.isoformat()
    # 時間の重なり。終了と開始が同じ時刻なのは重ならない。
    clash = db.execute(
        "SELECT 1 FROM studios_bookings WHERE cancelled = 0 AND room_code = ? AND date = ? "
        "AND start_min < ? AND end_min > ?",
        (room_code, date_text, end, start),
    ).fetchone()
    if clash:
        return "その時間は既に予約されています"
    count = db.execute(
        "SELECT COUNT(*) FROM studios_bookings WHERE cancelled = 0 AND employee_no = ? AND date = ?",
        (employee_no, date_text),
    ).fetchone()[0]
    if count >= SETTINGS["per_day_limit"]:
        return "1 人が 1 日に取れる予約の数を超えます"
    return None


@bp.route("/")
@login_required
def index():
    return render_index(date_text=request.args.get("date", "").strip())


@bp.route("/rooms/new", methods=["POST"])
@staff_required
def room_create():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    error = check_room_input(code, name)
    db = get_db()
    if error is None and db.execute("SELECT 1 FROM studios_rooms WHERE code = ?", (code,)).fetchone():
        error = "この部屋の番号は既に登録されています"
    if error:
        return render_index(error, 400)
    db.execute("INSERT INTO studios_rooms (code, name) VALUES (?, ?)", (code, name))
    audit.record("studios", "room_create", code)
    db.commit()
    return redirect("/studios/")


@bp.route("/rooms/edit", methods=["POST"])
@staff_required
def room_update():
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    error = check_room_input(code, name)
    db = get_db()
    if error is None and db.execute("SELECT 1 FROM studios_rooms WHERE code = ?", (code,)).fetchone() is None:
        error = "部屋が見つかりません"
    if error:
        return render_index(error, 400)
    db.execute("UPDATE studios_rooms SET name = ? WHERE code = ?", (name, code))
    audit.record("studios", "room_update", code)
    db.commit()
    return redirect("/studios/")


@bp.route("/book", methods=["POST"])
@staff_required
def book():
    form = request.form
    room_code = form.get("room_code", "").strip()
    employee_no = form.get("employee_no", "").strip()
    day = parse_date(form.get("date"))
    start = parse_time(form.get("start"))
    end = parse_time(form.get("end"))
    error = check_booking(room_code, employee_no, day, start, end)
    if error:
        return render_index(error, 400)
    db = get_db()
    cursor = db.execute(
        "INSERT INTO studios_bookings (room_code, employee_no, date, start_min, end_min) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, day.isoformat(), start, end),
    )
    audit.record("studios", "book", str(cursor.lastrowid))
    db.commit()
    return redirect("/studios/")


@bp.route("/cancel", methods=["POST"])
@staff_required
def cancel():
    booking_id = request.form.get("booking_id", "").strip()
    db = get_db()
    row = None
    if booking_id.isdigit():
        row = db.execute("SELECT id, cancelled FROM studios_bookings WHERE id = ?", (int(booking_id),)).fetchone()
    if row is None:
        return render_index("予約が見つかりません", 400)
    if row["cancelled"]:
        return render_index("この予約は既に取り消されています", 400)
    db.execute("UPDATE studios_bookings SET cancelled = 1 WHERE id = ?", (row["id"],))
    audit.record("studios", "cancel", str(row["id"]))
    db.commit()
    return redirect("/studios/")


@bp.route("/day")
@login_required
def day():
    date_text = request.args.get("date", "").strip()
    if parse_date(date_text) is None:
        return render_day(date_text, "日付は YYYY-MM-DD の形で入力してください", 400)
    return render_day(date_text)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(
        {
            "bookings": [
                {
                    "id": r["id"],
                    "room": r["room_code"],
                    "employee": r["employee_no"],
                    "date": r["date"],
                    "start": format_time(r["start_min"]),
                    "end": format_time(r["end_min"]),
                }
                for r in list_bookings()
            ]
        }
    )

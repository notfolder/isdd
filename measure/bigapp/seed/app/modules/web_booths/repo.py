"""Web 会議ブースの SQL。判定は service.py に任せ、ここは読み書きだけを行う。"""

from app.core.db import get_db


def list_rooms():
    return get_db().execute("SELECT code, name FROM web_booths_rooms ORDER BY code").fetchall()


def find_room(code):
    return get_db().execute("SELECT code, name FROM web_booths_rooms WHERE code = ?", (code,)).fetchone()


def insert_room(code, name):
    get_db().execute("INSERT INTO web_booths_rooms (code, name) VALUES (?, ?)", (code, name))


def update_room(code, name):
    get_db().execute("UPDATE web_booths_rooms SET name = ? WHERE code = ?", (name, code))


def find_employee(employee_no):
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()


def list_bookings(date=None):
    """取り消していない予約。date があればその日だけ。"""
    sql = "SELECT * FROM web_booths_bookings WHERE cancelled = 0"
    params = []
    if date:
        sql += " AND date = ?"
        params.append(date)
    sql += " ORDER BY date, room_code, start, id"
    return get_db().execute(sql, params).fetchall()


def list_bookings_by_id():
    return get_db().execute("SELECT * FROM web_booths_bookings WHERE cancelled = 0 ORDER BY id").fetchall()


def find_booking(booking_id):
    return get_db().execute("SELECT * FROM web_booths_bookings WHERE id = ?", (booking_id,)).fetchone()


def count_by_employee_on(employee_no, date):
    row = get_db().execute(
        "SELECT COUNT(*) FROM web_booths_bookings WHERE employee_no = ? AND date = ? AND cancelled = 0",
        (employee_no, date),
    ).fetchone()
    return row[0]


def count_overlapping(room_code, date, start, end):
    """同じ部屋・同じ日で時間が重なる予約の数。終了と開始が同じ時刻は重ならない。"""
    row = get_db().execute(
        "SELECT COUNT(*) FROM web_booths_bookings "
        "WHERE room_code = ? AND date = ? AND cancelled = 0 AND start < ? AND end > ?",
        (room_code, date, end, start),
    ).fetchone()
    return row[0]


def insert_booking(room_code, employee_no, date, start, end):
    get_db().execute(
        "INSERT INTO web_booths_bookings (room_code, employee_no, date, start, end) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, date, start, end),
    )


def cancel_booking(booking_id):
    get_db().execute("UPDATE web_booths_bookings SET cancelled = 1 WHERE id = ?", (booking_id,))

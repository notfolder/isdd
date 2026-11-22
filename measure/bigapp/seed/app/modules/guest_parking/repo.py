"""来客用駐車場の SQL。判定は service.py に任せ、ここは読み書きだけを行う。"""

from app.core.db import get_db


def find_room(code):
    return get_db().execute("SELECT code, name FROM guest_parking_rooms WHERE code = ?", (code,)).fetchone()


def list_rooms():
    return get_db().execute("SELECT code, name FROM guest_parking_rooms ORDER BY code").fetchall()


def insert_room(code, name):
    get_db().execute("INSERT INTO guest_parking_rooms (code, name) VALUES (?, ?)", (code, name))


def update_room(code, name):
    get_db().execute("UPDATE guest_parking_rooms SET name = ? WHERE code = ?", (name, code))


def find_active_employee(employee_no):
    """在籍している社員だけを返す（退職者は含めない）。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'",
        (employee_no,),
    ).fetchone()


def count_employee_bookings(employee_no, day):
    """その社員のその日の有効な（取り消していない）予約の数。"""
    return get_db().execute(
        "SELECT COUNT(*) FROM guest_parking_bookings WHERE employee_no = ? AND day = ? AND cancelled = 0",
        (employee_no, day),
    ).fetchone()[0]


def count_overlapping(room_code, day, start, end):
    """同じ部屋・同じ日で時間が重なる有効な予約の数。端が接するだけなら重ならない。"""
    return get_db().execute(
        "SELECT COUNT(*) FROM guest_parking_bookings "
        "WHERE room_code = ? AND day = ? AND cancelled = 0 AND start_time < ? AND end_time > ?",
        (room_code, day, end, start),
    ).fetchone()[0]


def insert_booking(room_code, employee_no, day, start, end):
    cur = get_db().execute(
        "INSERT INTO guest_parking_bookings (room_code, employee_no, day, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, day, start, end),
    )
    return cur.lastrowid


def find_booking(booking_id):
    return get_db().execute("SELECT * FROM guest_parking_bookings WHERE id = ?", (booking_id,)).fetchone()


def cancel_booking(booking_id):
    get_db().execute("UPDATE guest_parking_bookings SET cancelled = 1 WHERE id = ?", (booking_id,))


def list_bookings(day=None):
    """有効な予約を id の昇順で返す。day を渡すとその日だけ。"""
    sql = (
        "SELECT b.id, b.room_code, r.name AS room_name, b.employee_no, e.name AS employee_name, "
        "b.day, b.start_time, b.end_time "
        "FROM guest_parking_bookings b "
        "JOIN guest_parking_rooms r ON r.code = b.room_code "
        "LEFT JOIN employees e ON e.employee_no = b.employee_no "
        "WHERE b.cancelled = 0"
    )
    params = []
    if day:
        sql += " AND b.day = ?"
        params.append(day)
    sql += " ORDER BY b.id"
    return get_db().execute(sql, params).fetchall()

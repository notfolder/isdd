"""SQL をまとめた層。判定はここでは行わない。"""

from app.core.db import get_db


def get_room(code):
    return get_db().execute("SELECT * FROM massage_rooms_room WHERE code = ?", (code,)).fetchone()


def list_rooms():
    return get_db().execute("SELECT * FROM massage_rooms_room ORDER BY code").fetchall()


def insert_room(code, name):
    get_db().execute("INSERT INTO massage_rooms_room (code, name) VALUES (?, ?)", (code, name))


def update_room(code, name):
    get_db().execute("UPDATE massage_rooms_room SET name = ? WHERE code = ?", (name, code))


def get_employee(employee_no):
    return get_db().execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()


def get_booking(booking_id):
    return get_db().execute("SELECT * FROM massage_rooms_booking WHERE id = ?", (booking_id,)).fetchone()


def list_bookings(date=None):
    """取り消していない予約を、id の昇順で返す。date があればその日だけ。"""
    sql = "SELECT * FROM massage_rooms_booking WHERE cancelled = 0"
    params = []
    if date is not None:
        sql += " AND date = ?"
        params.append(date)
    return get_db().execute(sql + " ORDER BY id", params).fetchall()


def list_room_bookings(room_code, date):
    return get_db().execute(
        "SELECT * FROM massage_rooms_booking WHERE cancelled = 0 AND room_code = ? AND date = ?",
        (room_code, date),
    ).fetchall()


def count_employee_bookings(employee_no, date):
    return get_db().execute(
        "SELECT COUNT(*) FROM massage_rooms_booking WHERE cancelled = 0 AND employee_no = ? AND date = ?",
        (employee_no, date),
    ).fetchone()[0]


def insert_booking(room_code, employee_no, date, start_min, end_min):
    get_db().execute(
        "INSERT INTO massage_rooms_booking (room_code, employee_no, date, start_min, end_min) VALUES (?, ?, ?, ?, ?)",
        (room_code, employee_no, date, start_min, end_min),
    )


def cancel_booking(booking_id):
    get_db().execute("UPDATE massage_rooms_booking SET cancelled = 1 WHERE id = ?", (booking_id,))


def commit():
    get_db().commit()

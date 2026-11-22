"""屋上予約の SQL。"""

from app.core.db import get_db

SQL_ROOMS = "SELECT code, name FROM rooftop_rooms ORDER BY code"
SQL_ROOM = "SELECT code, name FROM rooftop_rooms WHERE code = ?"
SQL_ROOM_INSERT = "INSERT INTO rooftop_rooms (code, name) VALUES (?, ?)"
SQL_ROOM_UPDATE = "UPDATE rooftop_rooms SET name = ? WHERE code = ?"
SQL_EMPLOYEE = "SELECT employee_no, name, status FROM employees WHERE employee_no = ?"
SQL_BOOKINGS = """
SELECT b.id, b.room_code, r.name AS room_name, b.employee_no, e.name AS employee_name,
       b.date, b.start_min, b.end_min
FROM rooftop_bookings b
JOIN rooftop_rooms r ON r.code = b.room_code
LEFT JOIN employees e ON e.employee_no = b.employee_no
WHERE b.cancelled = 0 {where}
ORDER BY b.id
"""
SQL_ROOM_DAY = "SELECT start_min, end_min FROM rooftop_bookings WHERE cancelled = 0 AND room_code = ? AND date = ?"
SQL_PERSON_DAY_COUNT = "SELECT COUNT(*) FROM rooftop_bookings WHERE cancelled = 0 AND employee_no = ? AND date = ?"
SQL_BOOKING_INSERT = "INSERT INTO rooftop_bookings (room_code, employee_no, date, start_min, end_min) VALUES (?, ?, ?, ?, ?)"
SQL_BOOKING = "SELECT id, cancelled FROM rooftop_bookings WHERE id = ?"
SQL_BOOKING_CANCEL = "UPDATE rooftop_bookings SET cancelled = 1 WHERE id = ?"


def rooms():
    return get_db().execute(SQL_ROOMS).fetchall()


def get_room(code):
    return get_db().execute(SQL_ROOM, (code,)).fetchone()


def insert_room(code, name):
    get_db().execute(SQL_ROOM_INSERT, (code, name))


def update_room(code, name):
    get_db().execute(SQL_ROOM_UPDATE, (name, code))


def get_employee(number):
    return get_db().execute(SQL_EMPLOYEE, (number,)).fetchone()


def bookings(date=None):
    """取り消していない予約。date（YYYY-MM-DD）があればその日だけ。id の昇順。"""
    if date:
        return get_db().execute(SQL_BOOKINGS.format(where="AND b.date = ?"), (date,)).fetchall()
    return get_db().execute(SQL_BOOKINGS.format(where="")).fetchall()


def room_day_slots(room_code, date):
    return get_db().execute(SQL_ROOM_DAY, (room_code, date)).fetchall()


def person_day_count(employee_no, date):
    return get_db().execute(SQL_PERSON_DAY_COUNT, (employee_no, date)).fetchone()[0]


def insert_booking(room_code, employee_no, date, start, end):
    get_db().execute(SQL_BOOKING_INSERT, (room_code, employee_no, date, start, end))


def get_booking(booking_id):
    return get_db().execute(SQL_BOOKING, (booking_id,)).fetchone()


def cancel_booking(booking_id):
    get_db().execute(SQL_BOOKING_CANCEL, (booking_id,))

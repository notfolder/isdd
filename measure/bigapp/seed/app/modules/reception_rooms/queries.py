"""応接室の予約の SQL。"""

from app.core.db import get_db

SELECT_ROOMS = "SELECT code, name FROM reception_rooms_rooms ORDER BY code"
SELECT_ROOM = "SELECT code, name FROM reception_rooms_rooms WHERE code = ?"
INSERT_ROOM = "INSERT INTO reception_rooms_rooms (code, name) VALUES (?, ?)"
UPDATE_ROOM = "UPDATE reception_rooms_rooms SET name = ? WHERE code = ?"
# 在籍している社員だけを対象にする（総務規程 第 6 条）
SELECT_ACTIVE_EMPLOYEE = "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status = 'active'"
SELECT_BOOKINGS = """
SELECT b.id, b.room_code, r.name AS room_name, b.employee_no, e.name AS employee_name, b.date, b.start, b.end
FROM reception_rooms_bookings b
JOIN reception_rooms_rooms r ON r.code = b.room_code
LEFT JOIN employees e ON e.employee_no = b.employee_no
WHERE b.cancelled = 0 AND (? = '' OR b.date = ?)
ORDER BY b.date, b.start, b.room_code, b.id
"""
SELECT_STATUS = """
SELECT id, room_code, employee_no, date, start, end
FROM reception_rooms_bookings WHERE cancelled = 0 ORDER BY id
"""
SELECT_OVERLAP = """
SELECT 1 FROM reception_rooms_bookings
WHERE cancelled = 0 AND room_code = ? AND date = ? AND start < ? AND end > ?
"""
COUNT_PER_DAY = "SELECT COUNT(*) FROM reception_rooms_bookings WHERE cancelled = 0 AND employee_no = ? AND date = ?"
INSERT_BOOKING = "INSERT INTO reception_rooms_bookings (room_code, employee_no, date, start, end) VALUES (?, ?, ?, ?, ?)"
SELECT_BOOKING = "SELECT id FROM reception_rooms_bookings WHERE id = ? AND cancelled = 0"
CANCEL_BOOKING = "UPDATE reception_rooms_bookings SET cancelled = 1 WHERE id = ?"


def rooms():
    return get_db().execute(SELECT_ROOMS).fetchall()


def find_room(code):
    return get_db().execute(SELECT_ROOM, (code,)).fetchone()


def add_room(code, name):
    get_db().execute(INSERT_ROOM, (code, name))


def rename_room(code, name):
    get_db().execute(UPDATE_ROOM, (name, code))


def find_active_employee(employee_no):
    return get_db().execute(SELECT_ACTIVE_EMPLOYEE, (employee_no,)).fetchone()


def bookings(date_text=""):
    return get_db().execute(SELECT_BOOKINGS, (date_text, date_text)).fetchall()


def status_rows():
    return get_db().execute(SELECT_STATUS).fetchall()


def has_overlap(room_code, date_text, start, end):
    """start・end は HH:MM（0 埋め）。文字列の大小で時刻の前後が比べられる。"""
    return get_db().execute(SELECT_OVERLAP, (room_code, date_text, end, start)).fetchone() is not None


def count_for_day(employee_no, date_text):
    return get_db().execute(COUNT_PER_DAY, (employee_no, date_text)).fetchone()[0]


def add_booking(room_code, employee_no, date_text, start, end):
    cur = get_db().execute(INSERT_BOOKING, (room_code, employee_no, date_text, start, end))
    return cur.lastrowid


def find_booking(booking_id):
    return get_db().execute(SELECT_BOOKING, (booking_id,)).fetchone()


def cancel_booking(booking_id):
    get_db().execute(CANCEL_BOOKING, (booking_id,))

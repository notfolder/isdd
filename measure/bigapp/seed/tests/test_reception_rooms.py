"""応接室の予約のテスト。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/reception_rooms/rooms/new", data={"code": "R-1", "name": "応接 1"})
    admin.post("/reception_rooms/rooms/new", data={"code": "R-2", "name": "応接 2"})
    return admin


def book(client, start="09:00", end="10:00", date="2026-06-15", room="R-1", emp="100001"):
    return client.post("/reception_rooms/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(client):
    return client.get("/reception_rooms/status.json").get_json()["bookings"]


def audit_actions(app):
    with app.app_context():
        rows = get_db().execute("SELECT action FROM audit_log WHERE module = 'reception_rooms' ORDER BY id").fetchall()
    return [r["action"] for r in rows]


def test_room_create_and_duplicate(setup):
    r = setup.post("/reception_rooms/rooms/new", data={"code": "R-1", "name": "別名"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert "応接 1" in setup.get("/reception_rooms/").get_data(as_text=True)


def test_room_create_redirects_and_edit(setup):
    r = setup.post("/reception_rooms/rooms/new", data={"code": "R-3", "name": "大"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/reception_rooms/")
    r = setup.post("/reception_rooms/rooms/edit", data={"code": "R-3", "name": "小"})
    assert r.status_code == 302
    assert "小" in setup.get("/reception_rooms/").get_data(as_text=True)
    assert setup.post("/reception_rooms/rooms/edit", data={"code": "X", "name": "小"}).status_code == 400


def test_book_success_and_status_json(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/reception_rooms/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]


def test_unit_boundaries(setup):
    assert book(setup, "09:15", "10:00").status_code == 400
    assert book(setup, "09:00", "10:10").status_code == 400
    assert book(setup, "09:30", "10:00").status_code == 302


def test_business_hours_boundaries(setup):
    assert book(setup, "08:30", "09:30").status_code == 400
    assert book(setup, "17:30", "18:30").status_code == 400
    assert book(setup, "17:30", "18:00").status_code == 302
    assert book(setup, "09:00", "09:30", emp="100002").status_code == 302


def test_start_must_be_before_end(setup):
    assert book(setup, "10:00", "10:00").status_code == 400
    assert book(setup, "11:00", "10:00").status_code == 400


def test_bad_format_rejected(setup):
    assert book(setup, "abc", "10:00").status_code == 400
    assert book(setup, date="2026/06/15").status_code == 400
    assert book(setup, date="2026-02-30").status_code == 400


def test_overlap_rejected_adjacent_allowed(setup):
    assert book(setup, "10:00", "11:00").status_code == 302
    assert book(setup, "10:30", "11:30", emp="100002").status_code == 400
    assert book(setup, "09:30", "10:30", emp="100002").status_code == 400
    assert book(setup, "09:00", "10:00", emp="100002").status_code == 302
    assert book(setup, "11:00", "12:00", emp="100002").status_code == 302
    assert len(bookings(setup)) == 3


def test_overlap_only_same_room_and_day(setup):
    assert book(setup, "10:00", "11:00").status_code == 302
    assert book(setup, "10:00", "11:00", room="R-2", emp="100002").status_code == 302
    assert book(setup, "10:00", "11:00", date="2026-06-16", emp="100002").status_code == 302


def test_per_person_limit_two_per_day(setup):
    assert book(setup, "09:00", "09:30").status_code == 302
    assert book(setup, "10:00", "10:30", room="R-2").status_code == 302
    r = book(setup, "11:00", "11:30")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert book(setup, "11:00", "11:30", date="2026-06-16").status_code == 302
    assert book(setup, "11:00", "11:30", emp="100002").status_code == 302


def test_cancelled_booking_frees_slot_and_count(setup):
    book(setup, "09:00", "10:00")
    book(setup, "10:00", "11:00")
    assert book(setup, "12:00", "13:00").status_code == 400
    assert setup.post("/reception_rooms/cancel", data={"booking_id": "1"}).status_code == 302
    assert [b["id"] for b in bookings(setup)] == [2]
    assert book(setup, "09:00", "10:00").status_code == 302
    assert [b["id"] for b in bookings(setup)] == [2, 3]


def test_cancel_unknown_or_twice_is_400(setup):
    assert setup.post("/reception_rooms/cancel", data={"booking_id": "99"}).status_code == 400
    assert setup.post("/reception_rooms/cancel", data={"booking_id": "abc"}).status_code == 400
    book(setup)
    setup.post("/reception_rooms/cancel", data={"booking_id": "1"})
    assert setup.post("/reception_rooms/cancel", data={"booking_id": "1"}).status_code == 400


def test_past_date_rejected_today_allowed(setup):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302
    assert bookings(setup)[0]["date"] == "2026-06-15"


def test_today_follows_clock(setup, set_today):
    set_today("2026-07-01")
    assert book(setup, date="2026-06-30").status_code == 400
    assert book(setup, date="2026-07-01").status_code == 302


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert book(setup, emp="100002").status_code == 400
    assert book(setup, emp="999999").status_code == 400
    assert bookings(setup) == []


def test_unknown_room_rejected(setup):
    assert book(setup, room="NONE").status_code == 400


def test_staff_only_for_post(client, make_employee, setup):
    make_employee("100003", "一般")
    client.post("/logout")
    client.post("/login", data={"employee_no": "100003", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/reception_rooms/rooms/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert client.post("/reception_rooms/cancel", data={"booking_id": "1"}).status_code == 403
    assert client.get("/reception_rooms/status.json").status_code == 200
    assert client.get("/reception_rooms/").status_code == 200


def test_login_required(app):
    c = app.test_client()
    assert c.get("/reception_rooms/").status_code == 302
    assert c.get("/reception_rooms/status.json").status_code == 302
    assert c.post("/reception_rooms/book", data={}).status_code == 302


def test_date_filter_and_day_view(setup):
    book(setup, "09:00", "10:00")
    book(setup, "09:00", "10:00", date="2026-06-16", emp="100002")
    page = setup.get("/reception_rooms/?date=2026-06-16").get_data(as_text=True)
    assert 'data-booking-id="2"' in page and 'data-booking-id="1"' not in page
    day = setup.get("/reception_rooms/day?date=2026-06-15").get_data(as_text=True)
    assert "09:00-10:00" in day and "100001" in day
    assert setup.get("/reception_rooms/day?date=bad").status_code == 400


def test_audit_recorded_and_failure_not_recorded(app, setup):
    book(setup)
    book(setup, "09:15", "10:00")
    setup.post("/reception_rooms/rooms/edit", data={"code": "R-1", "name": "改"})
    setup.post("/reception_rooms/cancel", data={"booking_id": "1"})
    assert audit_actions(app) == ["room_create", "room_create", "book", "room_update", "cancel"]

"""仮眠室の予約のテスト。"""

import pytest


@pytest.fixture
def room(admin):
    admin.post("/nap_rooms/rooms/new", data={"code": "R-1", "name": "仮眠室1"})
    return "R-1"


def book(client, **kw):
    data = {"room_code": "R-1", "employee_no": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}
    data.update(kw)
    return client.post("/nap_rooms/book", data=data)


def bookings(client):
    return client.get("/nap_rooms/status.json").get_json()["bookings"]


def audit_actions(client):
    return [r["action"] for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "nap_rooms"]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_room_create_and_audit(admin):
    r = admin.post("/nap_rooms/rooms/new", data={"code": "R-1", "name": "仮眠室1"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/nap_rooms/")
    assert "仮眠室1" in admin.get("/nap_rooms/").get_data(as_text=True)
    assert audit_actions(admin) == ["room_create"]


def test_room_code_duplicate_rejected(admin, room):
    r = admin.post("/nap_rooms/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_room_edit(admin, room):
    assert admin.post("/nap_rooms/rooms/edit", data={"code": "R-1", "name": "新名称"}).status_code == 302
    assert "新名称" in admin.get("/nap_rooms/").get_data(as_text=True)
    assert "room_update" in audit_actions(admin)
    assert admin.post("/nap_rooms/rooms/edit", data={"code": "X", "name": "n"}).status_code == 400


def test_book_success_and_status_json(admin, room, emp):
    r = book(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/nap_rooms/")
    assert bookings(admin) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]
    assert "book" in audit_actions(admin)


def test_time_bounds_and_unit(admin, room, emp):
    assert book(admin, start="08:30", end="09:30").status_code == 400
    assert book(admin, start="17:30", end="18:30").status_code == 400
    assert book(admin, start="09:15", end="10:00").status_code == 400
    assert book(admin, start="09:00", end="10:10").status_code == 400
    assert bookings(admin) == []
    assert book(admin, start="17:30", end="18:00").status_code == 302


def test_start_must_be_before_end(admin, room, emp):
    assert book(admin, start="10:00", end="10:00").status_code == 400
    assert book(admin, start="11:00", end="10:00").status_code == 400


def test_overlap_rejected_adjacent_allowed(admin, room, make_employee, emp):
    make_employee("100002", "佐藤")
    make_employee("100003", "鈴木")
    assert book(admin, start="10:00", end="11:00").status_code == 302
    assert book(admin, employee_no="100002", start="10:30", end="11:30").status_code == 400
    assert book(admin, employee_no="100002", start="09:30", end="10:30").status_code == 400
    assert book(admin, employee_no="100002", start="09:00", end="10:00").status_code == 302
    assert book(admin, employee_no="100003", start="11:00", end="12:00").status_code == 302


def test_overlap_other_room_or_day_ok(admin, room, make_employee, emp):
    make_employee("100002", "佐藤")
    admin.post("/nap_rooms/rooms/new", data={"code": "R-2", "name": "仮眠室2"})
    assert book(admin).status_code == 302
    assert book(admin, employee_no="100002", room_code="R-2").status_code == 302


def test_one_booking_per_person_per_day(admin, room, emp):
    assert book(admin).status_code == 302
    assert book(admin, start="12:00", end="13:00").status_code == 400
    assert book(admin, date="2026-06-16", start="12:00", end="13:00").status_code == 302


def test_cancelled_booking_frees_slot_and_quota(admin, room, emp):
    book(admin)
    assert admin.post("/nap_rooms/cancel", data={"booking_id": "1"}).status_code == 302
    assert bookings(admin) == []
    assert "cancel" in audit_actions(admin)
    assert book(admin).status_code == 302


def test_cancel_unknown_or_twice(admin, room, emp):
    assert admin.post("/nap_rooms/cancel", data={"booking_id": "99"}).status_code == 400
    book(admin)
    admin.post("/nap_rooms/cancel", data={"booking_id": "1"})
    assert admin.post("/nap_rooms/cancel", data={"booking_id": "1"}).status_code == 400


def test_past_date_rejected_today_ok(admin, room, emp):
    assert book(admin, date="2026-06-14").status_code == 400
    assert book(admin, date="2026-06-15").status_code == 302


def test_past_date_follows_clock(admin, room, emp, set_today):
    set_today("2026-07-01")
    assert book(admin, date="2026-06-30").status_code == 400
    assert book(admin, date="2026-07-01").status_code == 302


def test_retired_and_unknown_employee_rejected(admin, room, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert book(admin).status_code == 400
    assert book(admin, employee_no="999999").status_code == 400
    assert bookings(admin) == []


def test_unknown_room_and_bad_date(admin, room, emp):
    assert book(admin, room_code="NOPE").status_code == 400
    assert book(admin, date="2026/06/15").status_code == 400
    assert book(admin, date="2026-02-30").status_code == 400


def test_rejection_leaves_no_audit(admin, room, emp):
    book(admin, start="09:15")
    assert "book" not in audit_actions(admin)


def test_non_staff_cannot_post(client, admin, room, make_employee):
    make_employee("100001", "山田")
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/nap_rooms/rooms/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert client.get("/nap_rooms/status.json").status_code == 200


def test_day_view_and_date_filter(admin, room, emp):
    book(admin)
    html = admin.get("/nap_rooms/day?date=2026-06-15").get_data(as_text=True)
    assert "R-1" in html and "09:00" in html
    assert "100001" in admin.get("/nap_rooms/?date=2026-06-15").get_data(as_text=True)
    assert "100001" not in admin.get("/nap_rooms/?date=2026-06-16").get_data(as_text=True).split("<h2>部屋</h2>")[0].split("<tbody>")[1]
    assert admin.get("/nap_rooms/day?date=xx").status_code == 400

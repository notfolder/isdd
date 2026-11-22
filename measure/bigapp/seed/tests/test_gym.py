"""トレーニングルームの予約のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/gym/rooms/new", data={"code": "R-1", "name": "ジム"})
    admin.post("/gym/rooms/new", data={"code": "R-2", "name": "ヨガ"})
    return admin


def book(c, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return c.post("/gym/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(c):
    return c.get("/gym/status.json").get_json()["bookings"]


def audit_rows(c):
    return [(r["module"], r["action"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "gym"]


def test_book_success_and_status(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/gym/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]


def test_room_code_unique(setup):
    r = setup.post("/gym/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)


def test_room_edit(setup):
    assert setup.post("/gym/rooms/edit", data={"code": "R-1", "name": "新ジム"}).status_code == 302
    assert "新ジム" in setup.get("/gym/").get_data(as_text=True)
    assert setup.post("/gym/rooms/edit", data={"code": "X", "name": "あ"}).status_code == 400


def test_thirty_minute_unit(setup):
    assert book(setup, start="09:15", end="10:00").status_code == 400
    assert book(setup, start="09:00", end="10:10").status_code == 400
    assert book(setup, start="09:30", end="10:30").status_code == 302


def test_business_hours_boundaries(setup):
    assert book(setup, start="08:30", end="09:30").status_code == 400
    assert book(setup, start="17:30", end="18:30").status_code == 400
    assert book(setup, start="17:30", end="18:00").status_code == 302
    assert book(setup, emp="100002", start="09:00", end="09:30").status_code == 302


def test_start_before_end(setup):
    assert book(setup, start="10:00", end="10:00").status_code == 400
    assert book(setup, start="11:00", end="10:00").status_code == 400


def test_overlap_rejected(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, emp="100002", start="10:30", end="11:30").status_code == 400
    assert book(setup, emp="100002", start="09:30", end="10:30").status_code == 400
    assert book(setup, emp="100002", start="10:00", end="11:00").status_code == 400
    assert len(bookings(setup)) == 1


def test_adjacent_is_not_overlap(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302


def test_other_room_or_day_not_overlap(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, room="R-2", emp="100002", start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", date="2026-06-16", start="10:00", end="11:00").status_code == 302


def test_one_booking_per_person_per_day(setup):
    book(setup)
    assert book(setup, room="R-2", start="13:00", end="14:00").status_code == 400
    assert book(setup, date="2026-06-16", start="13:00", end="14:00").status_code == 302


def test_cancel_frees_slot_and_limit(setup):
    book(setup)
    assert setup.post("/gym/cancel", data={"booking_id": "1"}).status_code == 302
    assert bookings(setup) == []
    assert book(setup).status_code == 302
    assert setup.post("/gym/cancel", data={"booking_id": "1"}).status_code == 400
    assert setup.post("/gym/cancel", data={"booking_id": "99"}).status_code == 400


def test_past_date_rejected_today_ok(setup):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302


def test_today_follows_clock(setup, set_today):
    set_today("2026-07-01")
    assert book(setup, date="2026-06-30").status_code == 400
    assert book(setup, date="2026-07-01").status_code == 302


def test_retired_and_unknown_employee(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert book(setup, emp="100002").status_code == 400
    assert book(setup, emp="999999").status_code == 400
    assert bookings(setup) == []


def test_unknown_room_and_bad_formats(setup):
    assert book(setup, room="ZZ").status_code == 400
    assert book(setup, date="2026-13-01").status_code == 400
    assert book(setup, date="abc").status_code == 400
    assert book(setup, start="9時", end="10:00").status_code == 400


def test_non_staff_cannot_change(setup, client, make_employee):
    from app import create_app  # noqa: F401
    setup.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/gym/cancel", data={"booking_id": "1"}).status_code == 403
    assert client.post("/gym/rooms/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert client.get("/gym/status.json").status_code == 200


def test_audit_recorded_only_on_success(setup):
    book(setup)
    book(setup, start="09:15")
    setup.post("/gym/cancel", data={"booking_id": "1"})
    setup.post("/gym/rooms/edit", data={"code": "R-1", "name": "新"})
    assert audit_rows(setup) == [("gym", "room_create")] * 2 + [("gym", "book"), ("gym", "cancel"), ("gym", "room_update")]


def test_list_filter_and_day_view(setup):
    book(setup)
    book(setup, emp="100002", date="2026-06-16")
    assert bookings(setup)[1]["id"] == 2
    page = setup.get("/gym/?date=2026-06-16").get_data(as_text=True)
    assert "100002" in page and "100001" not in page
    day = setup.get("/gym/day?date=2026-06-15")
    assert day.status_code == 200 and "ヨガ" in day.get_data(as_text=True)
    assert setup.get("/gym/day?date=bad").status_code == 400

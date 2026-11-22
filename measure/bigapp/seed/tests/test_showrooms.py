"""ショールームの予約のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/showrooms/rooms/new", data={"code": "R-1", "name": "第一"})
    admin.post("/showrooms/rooms/new", data={"code": "R-2", "name": "第二"})
    return admin


def book(c, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return c.post("/showrooms/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(c):
    return c.get("/showrooms/status.json").get_json()["bookings"]


def audit_rows(c):
    return [r for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "showrooms"]


def assert_rejected(response, c, before):
    assert response.status_code == 400
    assert '<p class="error">' in response.get_data(as_text=True)
    assert len(bookings(c)) == before


def test_book_success_and_status_json(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/showrooms/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]


def test_book_records_audit(setup):
    book(setup)
    assert [r["action"] for r in audit_rows(setup)] == ["room_create", "room_create", "book"]


def test_rejected_book_leaves_no_audit(setup):
    book(setup, start="09:10")
    assert [r["action"] for r in audit_rows(setup)] == ["room_create", "room_create"]


def test_unit_must_be_30_minutes(setup):
    assert_rejected(book(setup, start="09:15"), setup, 0)
    assert_rejected(book(setup, start="09:00", end="10:45"), setup, 0)
    assert book(setup, start="09:30", end="10:30").status_code == 302


def test_time_range_boundaries(setup):
    assert_rejected(book(setup, start="08:30", end="09:30"), setup, 0)
    assert_rejected(book(setup, start="17:30", end="18:30"), setup, 0)
    assert book(setup, start="09:00", end="09:30").status_code == 302
    assert book(setup, emp="100002", start="17:30", end="18:00").status_code == 302


def test_start_must_be_before_end(setup):
    assert_rejected(book(setup, start="10:00", end="10:00"), setup, 0)
    assert_rejected(book(setup, start="11:00", end="10:00"), setup, 0)


def test_bad_format_rejected(setup):
    assert_rejected(book(setup, date="2026/06/15"), setup, 0)
    assert_rejected(book(setup, start="9"), setup, 0)


def test_overlap_rejected_same_room(setup):
    book(setup, start="10:00", end="11:00")
    assert_rejected(book(setup, emp="100002", start="10:30", end="11:30"), setup, 1)
    assert_rejected(book(setup, emp="100002", start="09:30", end="10:30"), setup, 1)
    assert_rejected(book(setup, emp="100002", start="10:00", end="11:00"), setup, 1)


def test_adjacent_is_not_overlap(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302
    assert book(setup, emp="100002", start="09:00", end="10:00").status_code == 302


def test_other_room_or_day_is_not_overlap(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, room="R-2", emp="100002", start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", date="2026-06-16", start="10:00", end="11:00").status_code == 302


def test_daily_limit_two(setup):
    book(setup, start="09:00", end="10:00")
    book(setup, start="10:00", end="11:00")
    assert_rejected(book(setup, start="11:00", end="12:00"), setup, 2)
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302
    assert book(setup, date="2026-06-16").status_code == 302


def test_cancelled_booking_frees_slot_and_limit(setup):
    book(setup, start="09:00", end="10:00")
    book(setup, start="10:00", end="11:00")
    assert setup.post("/showrooms/cancel", data={"booking_id": "1"}).status_code == 302
    assert [b["id"] for b in bookings(setup)] == [2]
    assert book(setup, start="09:00", end="10:00").status_code == 302
    assert audit_rows(setup)[-2]["action"] == "cancel"


def test_cancel_unknown_or_twice(setup):
    assert_rejected(setup.post("/showrooms/cancel", data={"booking_id": "99"}), setup, 0)
    book(setup)
    setup.post("/showrooms/cancel", data={"booking_id": "1"})
    assert_rejected(setup.post("/showrooms/cancel", data={"booking_id": "1"}), setup, 0)


def test_past_date_rejected_today_ok(setup):
    assert_rejected(book(setup, date="2026-06-14"), setup, 0)
    assert book(setup, date="2026-06-15").status_code == 302


def test_past_judged_by_clock(setup, set_today):
    set_today("2026-07-01")
    assert_rejected(book(setup, date="2026-06-30"), setup, 0)
    assert book(setup, date="2026-07-01").status_code == 302


def test_retired_and_unknown_employee(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert_rejected(book(setup, emp="100002"), setup, 0)
    assert_rejected(book(setup, emp="999999"), setup, 0)


def test_unknown_room_rejected(setup):
    assert_rejected(book(setup, room="R-9"), setup, 0)


def test_room_code_unique_and_edit(setup):
    r = setup.post("/showrooms/rooms/new", data={"code": "R-1", "name": "重複"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert setup.post("/showrooms/rooms/edit", data={"code": "R-1", "name": "新名"}).status_code == 302
    assert "新名" in setup.get("/showrooms/").get_data(as_text=True)
    assert setup.post("/showrooms/rooms/edit", data={"code": "R-9", "name": "x"}).status_code == 400
    assert [r["action"] for r in audit_rows(setup)][-1] == "room_update"


def test_post_requires_staff(client, setup, make_employee):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/showrooms/cancel", data={"booking_id": "1"}).status_code == 403
    assert client.get("/showrooms/").status_code == 200
    assert client.get("/showrooms/status.json").status_code == 200


def test_login_required(client):
    assert client.get("/showrooms/status.json").status_code == 302
    assert client.get("/showrooms/day?date=2026-06-15").status_code == 302


def test_index_date_filter_and_day_view(setup):
    book(setup, date="2026-06-15")
    book(setup, emp="100002", date="2026-06-16")
    page = setup.get("/showrooms/?date=2026-06-16").get_data(as_text=True)
    assert "2026-06-16" in page and 'data-booking-id="1"' not in page
    day = setup.get("/showrooms/day?date=2026-06-15")
    assert day.status_code == 200 and "R-1" in day.get_data(as_text=True)
    assert setup.get("/showrooms/day?date=bad").status_code == 400

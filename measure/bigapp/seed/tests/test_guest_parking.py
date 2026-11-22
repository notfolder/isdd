"""来客用駐車場の予約のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/guest_parking/rooms/new", data={"code": "R-1", "name": "来客 1 番"})
    admin.post("/guest_parking/rooms/new", data={"code": "R-2", "name": "来客 2 番"})
    return admin


def book(c, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return c.post("/guest_parking/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(c):
    return c.get("/guest_parking/status.json").get_json()["bookings"]


def audit_rows(c):
    return [(r["module"], r["action"], r["target"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "guest_parking"]


def test_book_success_redirects_and_appears_in_status(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/guest_parking/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]


def test_book_is_audited(setup):
    book(setup)
    assert ("guest_parking", "book", "1") in audit_rows(setup)


def test_room_create_update_audited_and_duplicate_rejected(setup):
    r = setup.post("/guest_parking/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert setup.post("/guest_parking/rooms/edit", data={"code": "R-1", "name": "改名"}).status_code == 302
    assert "改名" in setup.get("/guest_parking/").get_data(as_text=True)
    rows = audit_rows(setup)
    assert ("guest_parking", "room_create", "R-1") in rows and ("guest_parking", "room_update", "R-1") in rows
    assert setup.post("/guest_parking/rooms/edit", data={"code": "R-9", "name": "x"}).status_code == 400


def test_post_requires_staff(client, setup, make_employee):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/guest_parking/cancel", data={"booking_id": "1"}).status_code == 403
    assert client.post("/guest_parking/rooms/new", data={"code": "R-3", "name": "x"}).status_code == 403
    assert client.get("/guest_parking/status.json").status_code == 200


@pytest.mark.parametrize("start,end", [("09:15", "10:00"), ("09:00", "10:10"), ("09:00", "09:45")])
def test_not_multiple_of_30_minutes_rejected(setup, start, end):
    r = book(setup, start=start, end=end)
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert bookings(setup) == []


def test_business_hours_boundaries(setup):
    assert book(setup, start="09:00", end="09:30").status_code == 302
    assert book(setup, room="R-2", start="17:30", end="18:00").status_code == 302
    assert book(setup, room="R-2", emp="100002", start="08:30", end="09:00").status_code == 400
    assert book(setup, room="R-2", emp="100002", start="18:00", end="18:30").status_code == 400
    assert book(setup, room="R-2", emp="100002", start="17:30", end="18:30").status_code == 400


def test_start_must_be_before_end(setup):
    assert book(setup, start="10:00", end="10:00").status_code == 400
    assert book(setup, start="11:00", end="10:00").status_code == 400


def test_overlap_rejected_but_adjacent_allowed(setup):
    assert book(setup, start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", start="10:30", end="11:30").status_code == 400
    assert book(setup, emp="100002", start="09:30", end="10:30").status_code == 400
    assert book(setup, emp="100002", start="10:00", end="11:00").status_code == 400
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302
    assert book(setup, emp="100002", start="09:00", end="10:00").status_code == 302


def test_same_time_in_other_room_or_day_allowed(setup):
    assert book(setup).status_code == 302
    assert book(setup, room="R-2", emp="100002").status_code == 302
    assert book(setup, emp="100002", date="2026-06-16").status_code == 302


def test_two_per_day_limit(setup):
    assert book(setup, start="09:00", end="10:00").status_code == 302
    assert book(setup, start="10:00", end="11:00").status_code == 302
    r = book(setup, start="11:00", end="12:00")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert book(setup, start="11:00", end="12:00", date="2026-06-16").status_code == 302


def test_cancel_frees_slot_and_limit(setup):
    book(setup, start="09:00", end="10:00")
    book(setup, start="10:00", end="11:00")
    r = setup.post("/guest_parking/cancel", data={"booking_id": "1"})
    assert r.status_code == 302
    assert [b["id"] for b in bookings(setup)] == [2]
    assert ("guest_parking", "cancel", "1") in audit_rows(setup)
    assert book(setup, start="09:00", end="10:00").status_code == 302
    assert setup.post("/guest_parking/cancel", data={"booking_id": "1"}).status_code == 400
    assert setup.post("/guest_parking/cancel", data={"booking_id": "abc"}).status_code == 400


def test_past_date_rejected_today_allowed(setup, set_today):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302
    set_today("2026-06-20")
    assert book(setup, emp="100002", date="2026-06-19").status_code == 400
    assert book(setup, emp="100002", date="2026-06-20").status_code == 302


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert book(setup, emp="100002").status_code == 400
    assert book(setup, emp="999999").status_code == 400
    assert bookings(setup) == []


def test_unknown_room_and_bad_formats_rejected(setup):
    assert book(setup, room="R-9").status_code == 400
    assert book(setup, date="2026/06/15").status_code == 400
    assert book(setup, date="2026-02-30").status_code == 400
    assert book(setup, start="9:00").status_code == 400
    assert book(setup, end="").status_code == 400


def test_rejected_booking_not_audited(setup):
    book(setup, start="09:10", end="10:00")
    assert not [r for r in audit_rows(setup) if r[1] == "book"]


def test_day_view_and_filter(setup):
    book(setup, start="10:00", end="11:00")
    book(setup, emp="100002", date="2026-06-16")
    day = setup.get("/guest_parking/day?date=2026-06-15").get_data(as_text=True)
    assert "R-1" in day and "R-2" in day and "10:00" in day
    assert setup.get("/guest_parking/day").status_code == 400
    page = setup.get("/guest_parking/?date=2026-06-16").get_data(as_text=True)
    assert 'data-booking-id="2"' in page and 'data-booking-id="1"' not in page
    assert setup.get("/guest_parking/?date=bad").status_code == 400


def test_status_json_ordered_by_id(setup):
    book(setup, room="R-2", start="10:00", end="11:00")
    book(setup, start="09:00", end="10:00")
    assert [b["id"] for b in bookings(setup)] == [1, 2]

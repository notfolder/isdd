"""Web 会議ブースの予約のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/web_booths/rooms/new", data={"code": "R-1", "name": "ブース 1"})
    admin.post("/web_booths/rooms/new", data={"code": "R-2", "name": "ブース 2"})
    return admin


def book(c, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return c.post("/web_booths/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(c):
    return c.get("/web_booths/status.json").get_json()["bookings"]


def audit_actions(c):
    return [r["action"] for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "web_booths"]


def test_book_success_redirects_and_listed(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/web_booths/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]


def test_room_code_duplicate_rejected(setup):
    r = setup.post("/web_booths/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_room_edit_and_unknown_room(setup):
    assert setup.post("/web_booths/rooms/edit", data={"code": "R-1", "name": "新名称"}).status_code == 302
    assert "新名称" in setup.get("/web_booths/").get_data(as_text=True)
    assert setup.post("/web_booths/rooms/edit", data={"code": "X", "name": "名"}).status_code == 400


def test_unit_must_be_30_minutes(setup):
    assert book(setup, start="09:15", end="10:00").status_code == 400
    assert book(setup, start="09:00", end="10:10").status_code == 400
    assert book(setup, start="09:30", end="10:30").status_code == 302


def test_hours_boundaries(setup):
    assert book(setup, start="08:30", end="09:30").status_code == 400
    assert book(setup, start="17:30", end="18:30").status_code == 400
    assert book(setup, start="17:30", end="18:00").status_code == 302
    assert book(setup, emp="100002", start="09:00", end="09:30").status_code == 302


def test_start_must_be_before_end(setup):
    assert book(setup, start="10:00", end="10:00").status_code == 400
    assert book(setup, start="11:00", end="10:00").status_code == 400


def test_overlap_rejected_but_adjacent_ok(setup):
    assert book(setup, start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", start="10:30", end="11:30").status_code == 400
    assert book(setup, emp="100002", start="09:30", end="10:30").status_code == 400
    assert book(setup, emp="100002", start="09:00", end="10:00").status_code == 302
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302


def test_other_room_or_day_not_overlap(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, room="R-2", emp="100002", start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", date="2026-06-16", start="10:00", end="11:00").status_code == 302


def test_max_three_per_day(setup):
    for s, e in [("09:00", "09:30"), ("10:00", "10:30"), ("11:00", "11:30")]:
        assert book(setup, start=s, end=e).status_code == 302
    assert book(setup, start="12:00", end="12:30").status_code == 400
    assert book(setup, date="2026-06-16", start="12:00", end="12:30").status_code == 302


def test_cancelled_booking_frees_slot_and_count(setup):
    for s, e in [("09:00", "09:30"), ("10:00", "10:30"), ("11:00", "11:30")]:
        book(setup, start=s, end=e)
    assert setup.post("/web_booths/cancel", data={"booking_id": "1"}).status_code == 302
    assert book(setup, start="09:00", end="09:30").status_code == 302
    assert all(b["id"] != 1 for b in bookings(setup))


def test_cancel_unknown_or_twice(setup):
    assert setup.post("/web_booths/cancel", data={"booking_id": "99"}).status_code == 400
    book(setup)
    setup.post("/web_booths/cancel", data={"booking_id": "1"})
    assert setup.post("/web_booths/cancel", data={"booking_id": "1"}).status_code == 400


def test_past_date_rejected_today_ok(setup):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert book(setup, emp="100002").status_code == 400
    assert book(setup, emp="999999").status_code == 400
    assert bookings(setup) == []


def test_unknown_room_and_bad_format(setup):
    assert book(setup, room="X").status_code == 400
    assert book(setup, date="2026/06/15").status_code == 400
    assert book(setup, start="9:00").status_code == 400


def test_non_staff_cannot_post(setup, client, make_employee):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/web_booths/rooms/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert client.get("/web_booths/status.json").status_code == 200


def test_audit_recorded_only_on_success(setup):
    book(setup)
    book(setup, start="09:15", end="10:00")
    setup.post("/web_booths/cancel", data={"booking_id": "1"})
    assert audit_actions(setup) == ["room_create", "room_create", "book", "cancel"]


def test_day_and_index_filter(setup):
    book(setup, date="2026-06-16")
    book(setup, emp="100002", date="2026-06-15")
    html = setup.get("/web_booths/day?date=2026-06-16").get_data(as_text=True)
    assert "09:00-10:00" in html and "100002" not in html
    assert setup.get("/web_booths/day").status_code == 400
    listed = setup.get("/web_booths/?date=2026-06-15").get_data(as_text=True)
    assert "100002" in listed and "2026-06-16" not in listed


def test_status_json_order(setup):
    book(setup, room="R-2", start="09:00", end="10:00")
    book(setup, start="09:00", end="10:00", emp="100002")
    assert [b["id"] for b in bookings(setup)] == [1, 2]

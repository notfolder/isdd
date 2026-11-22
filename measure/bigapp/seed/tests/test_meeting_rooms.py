"""会議室の予約のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/meeting_rooms/rooms/new", data={"code": "R-1", "name": "第一会議室"})
    admin.post("/meeting_rooms/rooms/new", data={"code": "R-2", "name": "第二会議室"})
    return admin


def book(c, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return c.post("/meeting_rooms/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(c):
    return c.get("/meeting_rooms/status.json").get_json()["bookings"]


def test_room_create_update_and_audit(setup):
    r = setup.post("/meeting_rooms/rooms/edit", data={"code": "R-1", "name": "改名"})
    assert r.status_code == 302
    assert "改名" in setup.get("/meeting_rooms/").get_data(as_text=True)
    actions = [(x["module"], x["action"], x["target"]) for x in setup.get("/audit.json").get_json()["rows"] if x["module"] == "meeting_rooms"]
    assert actions == [("meeting_rooms", "room_create", "R-1"), ("meeting_rooms", "room_create", "R-2"), ("meeting_rooms", "room_update", "R-1")]


def test_duplicate_room_code_rejected(setup):
    r = setup.post("/meeting_rooms/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_edit_unknown_room_rejected(setup):
    assert setup.post("/meeting_rooms/rooms/edit", data={"code": "X", "name": "名"}).status_code == 400


def test_book_success_and_status_json(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/meeting_rooms/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]
    assert ("meeting_rooms", "book", "1") in [(x["module"], x["action"], x["target"]) for x in setup.get("/audit.json").get_json()["rows"]]


def test_non_staff_cannot_post(setup, client, app):
    c = app.test_client()
    c.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(c).status_code == 403
    assert c.post("/meeting_rooms/rooms/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert c.get("/meeting_rooms/status.json").status_code == 200


def test_thirty_minute_unit(setup):
    assert book(setup, start="09:15", end="10:00").status_code == 400
    assert book(setup, start="09:00", end="09:45").status_code == 400
    assert book(setup, start="09:30", end="10:30").status_code == 302


def test_business_hours_boundaries(setup):
    assert book(setup, start="08:30", end="09:30").status_code == 400
    assert book(setup, start="17:30", end="18:30").status_code == 400
    assert book(setup, start="17:30", end="18:00").status_code == 302
    assert book(setup, room="R-2", start="09:00", end="09:30").status_code == 302


def test_start_must_be_before_end(setup):
    assert book(setup, start="10:00", end="10:00").status_code == 400
    assert book(setup, start="11:00", end="10:00").status_code == 400


def test_overlap_rejected_but_adjacent_ok(setup):
    assert book(setup, start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", start="10:30", end="11:30").status_code == 400
    assert book(setup, emp="100002", start="09:30", end="10:30").status_code == 400
    assert book(setup, emp="100002", start="10:30", end="11:00").status_code == 400
    assert book(setup, emp="100002", start="09:00", end="10:00").status_code == 302
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302
    assert book(setup, emp="100002", room="R-2", start="10:00", end="11:00").status_code == 302


def test_cancelled_booking_frees_slot(setup):
    book(setup)
    assert setup.post("/meeting_rooms/cancel", data={"booking_id": "1"}).status_code == 302
    assert bookings(setup) == []
    assert book(setup, emp="100002").status_code == 302
    assert setup.post("/meeting_rooms/cancel", data={"booking_id": "1"}).status_code == 400
    assert setup.post("/meeting_rooms/cancel", data={"booking_id": "99"}).status_code == 400


def test_max_three_per_day(setup):
    for s, e in [("09:00", "09:30"), ("09:30", "10:00"), ("10:00", "10:30")]:
        assert book(setup, start=s, end=e).status_code == 302
    r = book(setup, start="11:00", end="11:30")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert book(setup, date="2026-06-16", start="11:00", end="11:30").status_code == 302
    assert book(setup, emp="100002", start="11:00", end="11:30").status_code == 302


def test_cancel_reduces_daily_count(setup):
    for s, e in [("09:00", "09:30"), ("09:30", "10:00"), ("10:00", "10:30")]:
        book(setup, start=s, end=e)
    setup.post("/meeting_rooms/cancel", data={"booking_id": "1"})
    assert book(setup, start="11:00", end="11:30").status_code == 302


def test_past_date_rejected_today_ok(setup):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302


def test_past_uses_clock_today(setup, set_today):
    set_today("2026-07-01")
    assert book(setup, date="2026-06-30").status_code == 400
    assert book(setup, date="2026-07-01").status_code == 302


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert book(setup, emp="100002").status_code == 400
    assert book(setup, emp="999999").status_code == 400
    assert bookings(setup) == []


def test_unknown_room_and_bad_format_rejected(setup):
    assert book(setup, room="NONE").status_code == 400
    assert book(setup, date="2026/06/15").status_code == 400
    assert book(setup, start="9am").status_code == 400
    assert book(setup, date="").status_code == 400


def test_rejected_booking_changes_nothing(setup):
    book(setup, start="09:15")
    assert bookings(setup) == []
    rows = setup.get("/audit.json").get_json()["rows"]
    assert not [r for r in rows if r["action"] == "book"]


def test_day_view_and_date_filter(setup):
    book(setup)
    book(setup, date="2026-06-16", start="13:00", end="14:00")
    assert setup.get("/meeting_rooms/day").status_code == 400
    body = setup.get("/meeting_rooms/day?date=2026-06-16").get_data(as_text=True)
    assert "13:00" in body and "09:00" not in body
    lst = setup.get("/meeting_rooms/?date=2026-06-15").get_data(as_text=True)
    assert "09:00" in lst and "13:00" not in lst


def test_status_json_order_and_login_required(setup, app):
    book(setup, start="10:00", end="11:00")
    book(setup, start="09:00", end="10:00")
    assert [b["id"] for b in bookings(setup)] == [1, 2]
    assert app.test_client().get("/meeting_rooms/status.json").status_code == 302

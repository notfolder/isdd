"""集中ブースの予約のテスト。きまりを 1 つずつ確かめる。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/focus_booths/rooms/new", data={"code": "R-1", "name": "集中 1"})
    admin.post("/focus_booths/rooms/new", data={"code": "R-2", "name": "集中 2"})
    return admin


def book(c, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return c.post("/focus_booths/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(c):
    return c.get("/focus_booths/status.json").get_json()["bookings"]


def audit_actions(c):
    return [r["action"] for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "focus_booths"]


def test_room_create_and_duplicate(admin):
    assert admin.post("/focus_booths/rooms/new", data={"code": "R-1", "name": "A"}).status_code == 302
    r = admin.post("/focus_booths/rooms/new", data={"code": "R-1", "name": "B"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert audit_actions(admin) == ["room_create"]


def test_room_update(setup):
    assert setup.post("/focus_booths/rooms/edit", data={"code": "R-1", "name": "新名称"}).status_code == 302
    assert "新名称" in setup.get("/focus_booths/").get_data(as_text=True)
    assert setup.post("/focus_booths/rooms/edit", data={"code": "R-9", "name": "x"}).status_code == 400
    assert "room_update" in audit_actions(setup)


def test_book_success_and_status(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/focus_booths/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]
    assert "book" in audit_actions(setup)


def test_non_staff_cannot_post(setup, client, make_employee):
    setup.post("/logout")
    setup.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(setup).status_code == 403
    assert setup.post("/focus_booths/rooms/new", data={"code": "X", "name": "x"}).status_code == 403
    assert setup.get("/focus_booths/status.json").status_code == 200


def test_time_must_be_half_hour(setup):
    assert book(setup, start="09:15").status_code == 400
    assert book(setup, end="10:10").status_code == 400
    assert bookings(setup) == []


def test_time_range_boundaries(setup):
    assert book(setup, start="08:30", end="09:30").status_code == 400
    assert book(setup, start="17:30", end="18:30").status_code == 400
    assert book(setup, start="17:30", end="18:00").status_code == 302
    assert book(setup, emp="100002", start="09:00", end="09:30").status_code == 302


def test_start_must_be_before_end(setup):
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
    assert book(setup, emp="100002", start="09:00", end="10:00").status_code == 302


def test_other_room_or_day_is_free(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, room="R-2", emp="100002", start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", date="2026-06-16", start="10:00", end="11:00").status_code == 302


def test_daily_limit_four(setup):
    for i, s in enumerate(["09:00", "10:00", "11:00", "12:00"]):
        assert book(setup, start=s, end=f"{int(s[:2]):02d}:30").status_code == 302
    assert book(setup, start="13:00", end="13:30").status_code == 400
    assert book(setup, emp="100002", start="13:00", end="13:30").status_code == 302
    assert book(setup, date="2026-06-16", start="13:00", end="13:30").status_code == 302


def test_cancel_frees_slot_and_limit(setup):
    for s in ["09:00", "10:00", "11:00", "12:00"]:
        book(setup, start=s, end=f"{int(s[:2]):02d}:30")
    assert setup.post("/focus_booths/cancel", data={"booking_id": "1"}).status_code == 302
    assert [b["id"] for b in bookings(setup)] == [2, 3, 4]
    assert book(setup, start="09:00", end="09:30").status_code == 302
    assert "cancel" in audit_actions(setup)


def test_cancel_invalid(setup):
    book(setup)
    assert setup.post("/focus_booths/cancel", data={"booking_id": "99"}).status_code == 400
    setup.post("/focus_booths/cancel", data={"booking_id": "1"})
    assert setup.post("/focus_booths/cancel", data={"booking_id": "1"}).status_code == 400
    assert setup.post("/focus_booths/cancel", data={"booking_id": "abc"}).status_code == 400


def test_past_date_rejected_today_ok(setup):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302
    assert book(setup, date="2026-06-31").status_code == 400


def test_employee_must_be_active(setup, make_employee):
    make_employee("100003", "鈴木")
    setup.post("/employees/retire", data={"employee_no": "100003"})
    assert book(setup, emp="100003").status_code == 400
    assert book(setup, emp="999999").status_code == 400


def test_unknown_room_rejected(setup):
    assert book(setup, room="R-9").status_code == 400


def test_failure_changes_nothing(setup):
    before = audit_actions(setup)
    book(setup, start="09:15")
    assert audit_actions(setup) == before
    assert bookings(setup) == []


def test_pages(setup):
    book(setup, start="10:00", end="11:00")
    page = setup.get("/focus_booths/?date=2026-06-15").get_data(as_text=True)
    assert "<td>10:00</td>" in page
    assert "<td>10:00</td>" not in setup.get("/focus_booths/?date=2026-06-16").get_data(as_text=True)
    day = setup.get("/focus_booths/day?date=2026-06-15")
    assert day.status_code == 200 and "10:00-11:00" in day.get_data(as_text=True)

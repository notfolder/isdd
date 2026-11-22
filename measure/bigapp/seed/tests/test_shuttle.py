"""社用バスの予約のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/shuttle/rooms/new", data={"code": "R-1", "name": "1 号車"})
    return admin


def book(c, start="09:00", end="10:00", date="2026-06-15", room="R-1", emp="100001"):
    return c.post("/shuttle/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def test_book_success_and_status(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/shuttle/")
    data = setup.get("/shuttle/status.json").get_json()
    assert data == {"bookings": [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]}


def test_room_create_duplicate(setup):
    r = setup.post("/shuttle/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)


def test_room_update(setup):
    assert setup.post("/shuttle/rooms/edit", data={"code": "R-1", "name": "新名"}).status_code == 302
    assert "新名" in setup.get("/shuttle/").get_data(as_text=True)
    assert setup.post("/shuttle/rooms/edit", data={"code": "R-9", "name": "x"}).status_code == 400


def test_time_unit(setup):
    assert book(setup, "09:15", "10:00").status_code == 400
    assert book(setup, "09:00", "10:10").status_code == 400


def test_time_range_boundaries(setup):
    assert book(setup, "08:30", "09:30").status_code == 400
    assert book(setup, "17:30", "18:30").status_code == 400
    assert book(setup, "17:30", "18:00").status_code == 302
    assert book(setup, "09:00", "09:30", emp="100002").status_code == 302


def test_start_before_end(setup):
    assert book(setup, "10:00", "10:00").status_code == 400
    assert book(setup, "11:00", "10:00").status_code == 400


def test_overlap_rejected_adjacent_ok(setup):
    assert book(setup, "10:00", "11:00").status_code == 302
    assert book(setup, "10:30", "11:30", emp="100002").status_code == 400
    assert book(setup, "09:30", "10:30", emp="100002").status_code == 400
    assert book(setup, "09:00", "10:00", emp="100002").status_code == 302
    assert book(setup, "11:00", "12:00", emp="100002").status_code == 302


def test_other_room_or_day_not_overlap(setup):
    setup.post("/shuttle/rooms/new", data={"code": "R-2", "name": "2 号車"})
    assert book(setup).status_code == 302
    assert book(setup, room="R-2", emp="100002").status_code == 302
    assert book(setup, date="2026-06-16", emp="100002").status_code == 302


def test_max_two_per_day(setup):
    assert book(setup, "09:00", "10:00").status_code == 302
    assert book(setup, "10:00", "11:00").status_code == 302
    assert book(setup, "11:00", "12:00").status_code == 400
    assert book(setup, "11:00", "12:00", date="2026-06-16").status_code == 302


def test_cancel_frees_slot_and_count(setup):
    book(setup, "09:00", "10:00")
    book(setup, "10:00", "11:00")
    assert setup.post("/shuttle/cancel", data={"booking_id": "1"}).status_code == 302
    assert book(setup, "09:00", "10:00").status_code == 302
    assert setup.post("/shuttle/cancel", data={"booking_id": "1"}).status_code == 400
    ids = [b["id"] for b in setup.get("/shuttle/status.json").get_json()["bookings"]]
    assert ids == [2, 3]


def test_past_date(setup):
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
    assert book(setup, emp="100001").status_code == 302


def test_unknown_room(setup):
    assert book(setup, room="R-9").status_code == 400


def test_error_leaves_data_unchanged(setup):
    book(setup, "09:15", "10:00")
    assert setup.get("/shuttle/status.json").get_json() == {"bookings": []}


def test_staff_only_post(setup, client, make_employee):
    setup.post("/logout")
    setup.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(setup).status_code == 403
    assert setup.post("/shuttle/rooms/new", data={"code": "R-3", "name": "x"}).status_code == 403
    assert setup.get("/shuttle/status.json").status_code == 200


def test_audit_log(setup):
    book(setup)
    setup.post("/shuttle/cancel", data={"booking_id": "1"})
    rows = [(r["action"], r["target"]) for r in setup.get("/audit.json").get_json()["rows"] if r["module"] == "shuttle"]
    assert rows == [("room_create", "R-1"), ("book", "1"), ("cancel", "1")]


def test_day_and_filter(setup):
    book(setup, date="2026-06-15")
    book(setup, "10:00", "11:00", date="2026-06-16", emp="100002")
    assert "09:00-10:00" in setup.get("/shuttle/day?date=2026-06-15").get_data(as_text=True)
    page = setup.get("/shuttle/?date=2026-06-16").get_data(as_text=True)
    assert "100002" in page and "100001" not in page
    assert setup.get("/shuttle/day?date=bad").status_code == 400

"""屋上スペースの予約のテスト。今日は 2026-06-15（conftest）。"""

import pytest

DAY = "2026-06-20"


@pytest.fixture
def setup(admin, make_employee):
    admin.post("/rooftop/rooms/new", data={"code": "R-1", "name": "北側"})
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    return admin


def book(client, room="R-1", emp="100001", date=DAY, start="09:00", end="10:00"):
    return client.post("/rooftop/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(client):
    return client.get("/rooftop/status.json").get_json()["bookings"]


def audit_rows(client):
    return [(r["module"], r["action"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "rooftop"]


def test_book_success_and_status_json(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/rooftop/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": DAY, "start": "09:00", "end": "10:00"}]
    assert ("rooftop", "book") in audit_rows(setup)


def test_room_create_duplicate_and_update(setup):
    r = setup.post("/rooftop/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert setup.post("/rooftop/rooms/edit", data={"code": "R-1", "name": "南側"}).status_code == 302
    assert "南側" in setup.get("/rooftop/").get_data(as_text=True)
    assert setup.post("/rooftop/rooms/edit", data={"code": "X", "name": "南側"}).status_code == 400
    assert {a for _, a in audit_rows(setup)} == {"room_create", "room_update"}


def test_non_staff_cannot_post(setup, client, make_employee):
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/rooftop/rooms/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert client.get("/rooftop/status.json").status_code == 200


def test_login_required(app):
    c = app.test_client()
    assert c.get("/rooftop/status.json").status_code == 302


@pytest.mark.parametrize("start,end", [("09:30", "10:30"), ("09:00", "09:30"), ("09:00", "09:59")])
def test_slot_must_be_multiple_of_60(setup, start, end):
    assert book(setup, start=start, end=end).status_code == 400
    assert bookings(setup) == []


def test_business_hours_boundaries(setup):
    assert book(setup, start="08:00", end="09:00").status_code == 400
    assert book(setup, start="17:00", end="19:00").status_code == 400
    assert book(setup, start="09:00", end="18:00").status_code == 302
    assert book(setup, emp="100002", start="17:00", end="18:00", room="R-1", date="2026-06-21").status_code == 302


def test_start_must_be_before_end(setup):
    assert book(setup, start="10:00", end="10:00").status_code == 400
    assert book(setup, start="11:00", end="10:00").status_code == 400


def test_overlap_rejected_adjacent_allowed(setup):
    assert book(setup, start="10:00", end="12:00").status_code == 302
    r = book(setup, emp="100002", start="11:00", end="12:00")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert book(setup, emp="100002", start="09:00", end="11:00").status_code == 400
    assert book(setup, emp="100002", start="12:00", end="13:00").status_code == 302


def test_same_time_in_other_room_or_day_ok(setup):
    setup.post("/rooftop/rooms/new", data={"code": "R-2", "name": "南側"})
    book(setup, start="10:00", end="11:00")
    assert book(setup, room="R-2", emp="100002", start="10:00", end="11:00").status_code == 302
    assert len(bookings(setup)) == 2


def test_one_booking_per_person_per_day(setup):
    assert book(setup, start="09:00", end="10:00").status_code == 302
    assert book(setup, start="13:00", end="14:00").status_code == 400
    assert book(setup, start="13:00", end="14:00", date="2026-06-21").status_code == 302


def test_past_date_rejected_today_ok(setup):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302


def test_employee_must_be_active_and_exist(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert book(setup, emp="100002").status_code == 400
    assert book(setup, emp="999999").status_code == 400
    assert book(setup, room="NOPE").status_code == 400


def test_bad_date_format_rejected(setup):
    assert book(setup, date="2026/06/20").status_code == 400
    assert book(setup, date="2026-02-30").status_code == 400
    assert book(setup, start="9:00").status_code == 400


def test_cancel_frees_slot_and_limit(setup):
    book(setup)
    assert setup.post("/rooftop/cancel", data={"booking_id": "1"}).status_code == 302
    assert bookings(setup) == []
    assert ("rooftop", "cancel") in audit_rows(setup)
    assert book(setup, emp="100001").status_code == 302
    assert setup.post("/rooftop/cancel", data={"booking_id": "1"}).status_code == 400
    assert setup.post("/rooftop/cancel", data={"booking_id": "abc"}).status_code == 400


def test_failed_operations_leave_no_audit(setup):
    before = len(audit_rows(setup))
    book(setup, start="09:30", end="10:30")
    assert len(audit_rows(setup)) == before


def test_index_date_filter_and_day_view(setup):
    book(setup)
    book(setup, emp="100002", date="2026-06-21", start="10:00", end="11:00")
    body = setup.get(f"/rooftop/?date={DAY}").get_data(as_text=True)
    assert "100001" in body and "100002" not in body
    day = setup.get(f"/rooftop/day?date={DAY}")
    assert day.status_code == 200 and "R-1" in day.get_data(as_text=True)
    assert setup.get("/rooftop/day?date=bad").status_code == 400

"""マッサージ室の予約のテスト。きまりを 1 つずつ確かめる。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/massage_rooms/rooms/new", data={"code": "R-1", "name": "第一"})
    admin.post("/massage_rooms/rooms/new", data={"code": "R-2", "name": "第二"})
    return admin


def book(client, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return client.post(
        "/massage_rooms/book",
        data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end},
    )


def count(app):
    with app.app_context():
        return get_db().execute("SELECT COUNT(*) FROM massage_rooms_booking").fetchone()[0]


def actions(app):
    with app.app_context():
        rows = get_db().execute("SELECT action FROM audit_log WHERE module = 'massage_rooms' ORDER BY id").fetchall()
    return [r["action"] for r in rows]


def test_book_success_redirects_and_records(setup, app):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/massage_rooms/")
    assert count(app) == 1
    assert actions(app)[-1] == "book"


def test_room_create_duplicate_code_rejected(setup, app):
    r = setup.post("/massage_rooms/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert actions(app).count("room_create") == 2


def test_room_update_changes_name(setup, app):
    r = setup.post("/massage_rooms/rooms/edit", data={"code": "R-1", "name": "改名"})
    assert r.status_code == 302
    assert "改名" in setup.get("/massage_rooms/").get_data(as_text=True)
    assert actions(app)[-1] == "room_update"
    assert setup.post("/massage_rooms/rooms/edit", data={"code": "XX", "name": "a"}).status_code == 400


def test_start_must_be_multiple_of_30(setup, app):
    assert book(setup, start="09:15", end="10:00").status_code == 400
    assert book(setup, start="09:00", end="10:10").status_code == 400
    assert count(app) == 0


def test_time_range_boundaries(setup, app):
    assert book(setup, start="08:30", end="09:30").status_code == 400
    assert book(setup, start="17:30", end="18:30").status_code == 400
    assert book(setup, start="09:00", end="09:30").status_code == 302
    assert book(setup, emp="100002", start="17:30", end="18:00").status_code == 302


def test_start_must_be_before_end(setup):
    assert book(setup, start="10:00", end="10:00").status_code == 400
    assert book(setup, start="11:00", end="10:00").status_code == 400


def test_overlap_rejected(setup, app):
    assert book(setup, start="10:00", end="11:00").status_code == 302
    for s, e in [("10:00", "11:00"), ("09:30", "10:30"), ("10:30", "11:30"), ("09:30", "11:30")]:
        assert book(setup, emp="100002", start=s, end=e).status_code == 400
    assert count(app) == 1


def test_adjacent_is_not_overlap(setup, app):
    assert book(setup, start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302
    assert count(app) == 2


def test_other_room_or_other_day_not_overlap(setup):
    assert book(setup, start="10:00", end="11:00").status_code == 302
    assert book(setup, room="R-2", emp="100002", start="10:00", end="11:00").status_code == 302
    assert book(setup, emp="100002", date="2026-06-16", start="10:00", end="11:00").status_code == 302


def test_one_booking_per_day_per_employee(setup, app):
    assert book(setup, start="09:00", end="09:30").status_code == 302
    assert book(setup, room="R-2", start="12:00", end="12:30").status_code == 400
    assert book(setup, date="2026-06-16", start="12:00", end="12:30").status_code == 302
    assert count(app) == 2


def test_cancel_frees_slot_and_daily_limit(setup, app):
    book(setup, start="09:00", end="10:00")
    assert setup.post("/massage_rooms/cancel", data={"booking_id": "1"}).status_code == 302
    assert actions(app)[-1] == "cancel"
    assert book(setup, start="09:00", end="10:00").status_code == 302
    assert setup.post("/massage_rooms/cancel", data={"booking_id": "1"}).status_code == 400
    assert setup.post("/massage_rooms/cancel", data={"booking_id": "99"}).status_code == 400


def test_past_date_rejected_today_ok(setup, set_today):
    assert book(setup, date="2026-06-14").status_code == 400
    assert book(setup, date="2026-06-15").status_code == 302
    set_today("2026-06-20")
    assert book(setup, emp="100002", date="2026-06-19").status_code == 400


def test_retired_and_unknown_employee_rejected(setup, app):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert book(setup, emp="100002").status_code == 400
    assert book(setup, emp="999999").status_code == 400
    assert count(app) == 0


def test_unknown_room_and_bad_formats_rejected(setup):
    assert book(setup, room="ZZ").status_code == 400
    assert book(setup, date="2026/06/15").status_code == 400
    assert book(setup, date="2026-02-30").status_code == 400
    assert book(setup, start="9am").status_code == 400


def test_only_staff_can_change_data(setup, client, app):
    client.get("/logout")
    with client.session_transaction() as s:
        s.clear()
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/massage_rooms/rooms/new", data={"code": "X", "name": "x"}).status_code == 403
    assert client.post("/massage_rooms/cancel", data={"booking_id": "1"}).status_code == 403
    assert client.get("/massage_rooms/status.json").status_code == 200


def test_status_json_shape_and_cancelled_excluded(setup):
    book(setup, start="09:00", end="10:00")
    book(setup, room="R-2", emp="100002", start="10:00", end="10:30")
    setup.post("/massage_rooms/cancel", data={"booking_id": "2"})
    data = setup.get("/massage_rooms/status.json").get_json()
    assert data == {"bookings": [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]}


def test_list_filter_by_date_and_day_view(setup):
    book(setup, date="2026-06-15")
    book(setup, emp="100002", date="2026-06-16")
    page = setup.get("/massage_rooms/?date=2026-06-16").get_data(as_text=True)
    assert "100002" in page and "100001" not in page
    day = setup.get("/massage_rooms/day?date=2026-06-15").get_data(as_text=True)
    assert "R-1" in day and "100001" in day
    assert setup.get("/massage_rooms/day?date=bad").status_code == 400

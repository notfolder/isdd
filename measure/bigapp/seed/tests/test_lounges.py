"""ラウンジの貸切の予約のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    admin.post("/lounges/rooms/new", data={"code": "R-1", "name": "ラウンジ 1"})
    admin.post("/lounges/rooms/new", data={"code": "R-2", "name": "ラウンジ 2"})
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    return admin


def book(c, room="R-1", no="100001", date="2026-06-15", start="09:00", end="10:00"):
    return c.post("/lounges/book", data={"room_code": room, "employee_no": no, "date": date, "start": start, "end": end})


def bookings(c):
    return c.get("/lounges/status.json").get_json()["bookings"]


def audit_actions(c):
    return [(r["module"], r["action"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "lounges"]


def assert_rejected(response, c=None, count=None):
    assert response.status_code == 400
    assert '<p class="error">' in response.get_data(as_text=True)
    if count is not None:
        assert len(bookings(c)) == count


def test_book_success_and_status_json(setup):
    r = book(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/lounges/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]


def test_book_today_ok_past_rejected(setup):
    assert book(setup, date="2026-06-15").status_code == 302
    assert_rejected(book(setup, no="100002", date="2026-06-14"), setup, 1)


def test_time_boundaries(setup):
    assert book(setup, start="09:00", end="18:00").status_code == 302
    assert_rejected(book(setup, no="100002", start="08:00", end="09:00"), setup, 1)
    assert_rejected(book(setup, no="100002", start="17:00", end="19:00"), setup, 1)
    assert_rejected(book(setup, no="100002", start="18:00", end="19:00"), setup, 1)


def test_start_must_be_before_end(setup):
    assert_rejected(book(setup, start="11:00", end="10:00"), setup, 0)
    assert_rejected(book(setup, start="10:00", end="10:00"), setup, 0)


def test_sixty_minute_unit(setup):
    assert_rejected(book(setup, start="09:30", end="10:30"), setup, 0)
    assert_rejected(book(setup, start="09:00", end="10:30"), setup, 0)
    assert_rejected(book(setup, start="09:00", end="09:59"), setup, 0)
    assert book(setup, start="10:00", end="12:00").status_code == 302


def test_bad_format(setup):
    assert_rejected(book(setup, date="2026/06/20"), setup, 0)
    assert_rejected(book(setup, start="9am"), setup, 0)
    assert_rejected(book(setup, date=""), setup, 0)


def test_overlap_same_room_rejected(setup):
    book(setup, start="10:00", end="12:00")
    assert_rejected(book(setup, no="100002", start="11:00", end="13:00"), setup, 1)
    assert_rejected(book(setup, no="100002", start="09:00", end="11:00"), setup, 1)
    assert_rejected(book(setup, no="100002", start="10:00", end="12:00"), setup, 1)


def test_adjacent_is_not_overlap(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, no="100002", start="11:00", end="12:00").status_code == 302
    assert len(bookings(setup)) == 2


def test_other_room_or_other_day_not_overlap(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, room="R-2", no="100002", start="10:00", end="11:00").status_code == 302
    assert len(bookings(setup)) == 2


def test_one_booking_per_person_per_day(setup):
    book(setup, start="09:00", end="10:00")
    assert_rejected(book(setup, room="R-2", start="13:00", end="14:00"), setup, 1)
    assert book(setup, date="2026-06-16").status_code == 302


def test_cancel_frees_slot_and_quota(setup):
    book(setup)
    assert setup.post("/lounges/cancel", data={"booking_id": "1"}).status_code == 302
    assert bookings(setup) == []
    assert book(setup).status_code == 302
    assert [b["id"] for b in bookings(setup)] == [2]


def test_cancel_unknown_or_twice_rejected(setup):
    assert_rejected(setup.post("/lounges/cancel", data={"booking_id": "99"}), setup)
    book(setup)
    setup.post("/lounges/cancel", data={"booking_id": "1"})
    assert_rejected(setup.post("/lounges/cancel", data={"booking_id": "1"}), setup)
    assert_rejected(setup.post("/lounges/cancel", data={"booking_id": "abc"}), setup)


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert_rejected(book(setup, no="100002"), setup, 0)
    assert_rejected(book(setup, no="999999"), setup, 0)


def test_unknown_room_rejected(setup):
    assert_rejected(book(setup, room="R-9"), setup, 0)


def test_room_code_unique_and_update(setup):
    assert_rejected(setup.post("/lounges/rooms/new", data={"code": "R-1", "name": "別名"}))
    assert_rejected(setup.post("/lounges/rooms/new", data={"code": "", "name": "x"}))
    assert setup.post("/lounges/rooms/edit", data={"code": "R-1", "name": "新しい名前"}).status_code == 302
    assert "新しい名前" in setup.get("/lounges/day?date=2026-06-15").get_data(as_text=True)
    assert_rejected(setup.post("/lounges/rooms/edit", data={"code": "R-9", "name": "x"}))


def test_staff_only_for_post(setup, make_employee, client):
    make_employee("100003", "一般")
    c = client
    c.post("/logout")
    c.post("/login", data={"employee_no": "100003", "password": "password1"})
    assert book(c).status_code == 403
    assert c.post("/lounges/cancel", data={"booking_id": "1"}).status_code == 403
    assert c.post("/lounges/rooms/new", data={"code": "X", "name": "x"}).status_code == 403
    assert c.get("/lounges/status.json").status_code == 200
    assert c.get("/lounges/").status_code == 200


def test_not_logged_in_redirected(client):
    assert client.get("/lounges/status.json").status_code == 302
    assert client.post("/lounges/book", data={}).status_code == 302


def test_audit_recorded_only_on_success(setup):
    book(setup)
    book(setup, start="09:30")
    setup.post("/lounges/cancel", data={"booking_id": "1"})
    setup.post("/lounges/rooms/edit", data={"code": "R-1", "name": "改名"})
    actions = [a for _, a in audit_actions(setup)]
    assert actions.count("room_create") == 2
    assert actions.count("book") == 1
    assert actions.count("cancel") == 1
    assert actions.count("room_update") == 1


def test_index_date_filter_and_day_view(setup):
    book(setup, date="2026-06-15")
    book(setup, no="100002", date="2026-06-16")
    html = setup.get("/lounges/?date=2026-06-16").get_data(as_text=True)
    assert 'data-booking-id="2"' in html and 'data-booking-id="1"' not in html
    day = setup.get("/lounges/day?date=2026-06-15").get_data(as_text=True)
    assert "R-1" in day and "R-2" in day and "100001" in day and "100002" not in day
    assert setup.get("/lounges/day?date=bad").status_code == 400


def test_today_follows_clock(setup, set_today):
    set_today("2026-07-01")
    assert_rejected(book(setup, date="2026-06-30"), setup, 0)
    assert book(setup, date="2026-07-01").status_code == 302

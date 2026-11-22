"""実験室の予約のテスト。"""

import pytest

from app.core.db import ADMIN_NO


@pytest.fixture
def lab(admin, make_employee):
    """部屋 R-1 と在籍の社員 100001・100002 がある状態。"""
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/labs/rooms/new", data={"code": "R-1", "name": "第一実験室"})
    return admin


def book(client, start="09:00", end="10:00", date="2026-06-15", room="R-1", emp="100001"):
    return client.post("/labs/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def bookings(client):
    return client.get("/labs/status.json").get_json()["bookings"]


def test_book_success_and_status_json(lab):
    response = book(lab)
    assert response.status_code == 302 and response.headers["Location"].endswith("/labs/")
    assert bookings(lab) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]


def test_only_staff_can_post(lab, make_employee, client):
    lab.post("/logout")
    lab.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(lab).status_code == 403
    assert lab.post("/labs/rooms/new", data={"code": "R-2", "name": "x"}).status_code == 403
    assert lab.get("/labs/status.json").status_code == 200
    assert bookings(lab) == []


def test_non_hour_times_rejected(lab):
    for start, end in [("09:30", "10:30"), ("09:00", "10:30"), ("09:15", "10:00")]:
        response = book(lab, start, end)
        assert response.status_code == 400 and '<p class="error">' in response.get_data(as_text=True)
    assert bookings(lab) == []


def test_business_hours_boundaries(lab):
    assert book(lab, "08:00", "09:00").status_code == 400
    assert book(lab, "18:00", "19:00").status_code == 400
    assert book(lab, "17:00", "19:00").status_code == 400
    assert book(lab, "09:00", "10:00").status_code == 302
    assert book(lab, "17:00", "18:00").status_code == 302


def test_start_must_be_before_end(lab):
    assert book(lab, "10:00", "10:00").status_code == 400
    assert book(lab, "11:00", "10:00").status_code == 400


def test_overlap_rejected_but_adjacent_allowed(lab):
    assert book(lab, "10:00", "12:00").status_code == 302
    assert book(lab, "11:00", "12:00").status_code == 400
    assert book(lab, "09:00", "11:00", emp="100002").status_code == 400
    assert book(lab, "09:00", "10:00", emp="100002").status_code == 302
    assert book(lab, "12:00", "13:00", emp="100001").status_code == 302  # 直前の予約の終了と同じ時刻の開始
    assert len(bookings(lab)) == 3


def test_overlap_only_same_room_and_same_day(lab):
    lab.post("/labs/rooms/new", data={"code": "R-2", "name": "第二"})
    assert book(lab, "10:00", "11:00").status_code == 302
    assert book(lab, "10:00", "11:00", room="R-2", emp="100002").status_code == 302
    assert book(lab, "10:00", "11:00", date="2026-06-16", emp="100002").status_code == 302


def test_adjacent_boundary_exact(lab):
    assert book(lab, "09:00", "10:00").status_code == 302
    assert book(lab, "10:00", "11:00", emp="100002").status_code == 302
    assert book(lab, "08:00", "09:00", emp="100002").status_code == 400  # 営業時間外


def test_two_bookings_per_day_limit(lab):
    assert book(lab, "09:00", "10:00").status_code == 302
    assert book(lab, "10:00", "11:00").status_code == 302
    assert book(lab, "11:00", "12:00").status_code == 400
    assert book(lab, "11:00", "12:00", date="2026-06-16").status_code == 302  # 別の日はよい
    assert book(lab, "11:00", "12:00", emp="100002").status_code == 302  # 別の社員はよい


def test_cancelled_booking_frees_limit_and_slot(lab):
    book(lab, "09:00", "10:00")
    book(lab, "10:00", "11:00")
    assert lab.post("/labs/cancel", data={"booking_id": "1"}).status_code == 302
    assert [b["id"] for b in bookings(lab)] == [2]
    assert book(lab, "09:00", "10:00", emp="100002").status_code == 302
    assert book(lab, "12:00", "13:00").status_code == 302


def test_past_date_rejected_today_allowed(lab):
    assert book(lab, date="2026-06-14").status_code == 400
    assert book(lab, date="2026-06-15").status_code == 302


def test_today_follows_clock(lab, set_today):
    set_today("2026-07-01")
    assert book(lab, date="2026-06-30").status_code == 400
    assert book(lab, date="2026-07-01").status_code == 302


def test_retired_and_unknown_employee_rejected(lab):
    lab.post("/employees/retire", data={"employee_no": "100002"})
    assert book(lab, emp="100002").status_code == 400
    assert book(lab, emp="999999").status_code == 400
    assert book(lab, emp=ADMIN_NO).status_code == 302


def test_unknown_room_and_bad_date_rejected(lab):
    assert book(lab, room="NONE").status_code == 400
    assert book(lab, date="2026-13-01").status_code == 400
    assert book(lab, date="").status_code == 400


def test_room_code_unique_and_update(lab):
    response = lab.post("/labs/rooms/new", data={"code": "R-1", "name": "重複"})
    assert response.status_code == 400 and "error" in response.get_data(as_text=True)
    assert lab.post("/labs/rooms/edit", data={"code": "R-1", "name": "新しい名前"}).status_code == 302
    assert "新しい名前" in lab.get("/labs/").get_data(as_text=True)
    assert lab.post("/labs/rooms/edit", data={"code": "R-9", "name": "x"}).status_code == 400


def test_cancel_unknown_or_twice_rejected(lab):
    book(lab)
    assert lab.post("/labs/cancel", data={"booking_id": "99"}).status_code == 400
    assert lab.post("/labs/cancel", data={"booking_id": "1"}).status_code == 302
    assert lab.post("/labs/cancel", data={"booking_id": "1"}).status_code == 400


def test_failed_operation_leaves_no_data_or_audit(lab):
    before = len(lab.get("/audit.json").get_json()["rows"])
    book(lab, "09:30", "10:30")
    assert len(lab.get("/audit.json").get_json()["rows"]) == before
    assert bookings(lab) == []


def test_audit_actions_recorded(lab):
    book(lab)
    lab.post("/labs/rooms/edit", data={"code": "R-1", "name": "改名"})
    lab.post("/labs/cancel", data={"booking_id": "1"})
    rows = [(r["action"], r["target"]) for r in lab.get("/audit.json").get_json()["rows"] if r["module"] == "labs"]
    assert rows == [("room_create", "R-1"), ("book", "1"), ("room_update", "R-1"), ("cancel", "1")]


def test_pages_and_date_filter(lab):
    book(lab, date="2026-06-15")
    book(lab, "11:00", "12:00", date="2026-06-16", emp="100002")
    html = lab.get("/labs/?date=2026-06-16").get_data(as_text=True)
    assert "2026-06-16" in html and 'data-booking-id="1"' not in html
    day = lab.get("/labs/day?date=2026-06-15")
    assert day.status_code == 200 and "09:00-10:00" in day.get_data(as_text=True)
    assert lab.get("/labs/day?date=bad").status_code == 400


def test_login_required_for_views(client):
    assert client.get("/labs/").status_code == 302
    assert client.get("/labs/status.json").status_code == 302

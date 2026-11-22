"""研修室の予約のテスト。きまりを 1 つずつ確かめる。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/seminar_rooms/rooms/new", data={"code": "R-1", "name": "第 1 研修室"})
    admin.post("/seminar_rooms/rooms/new", data={"code": "R-2", "name": "第 2 研修室"})
    return admin


def book(client, room="R-1", emp="100001", date="2026-06-15", start="09:00", end="10:00"):
    return client.post("/seminar_rooms/book", data={"room_code": room, "employee_no": emp, "date": date, "start": start, "end": end})


def error_of(response):
    assert response.status_code == 400
    assert 'class="error"' in response.get_data(as_text=True)


def bookings(client):
    return client.get("/seminar_rooms/status.json").get_json()["bookings"]


def test_予約できて一覧と_json_に出る(setup):
    response = book(setup)
    assert response.status_code == 302 and response.headers["Location"].endswith("/seminar_rooms/")
    assert bookings(setup) == [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]
    assert "100001" in setup.get("/seminar_rooms/").get_data(as_text=True)


def test_60分の倍数でない時刻は受け付けない(setup):
    error_of(book(setup, start="09:30", end="10:30"))
    error_of(book(setup, start="09:00", end="10:30"))
    assert bookings(setup) == []


def test_9時から18時の境界(setup):
    assert book(setup, start="09:00", end="10:00").status_code == 302
    assert book(setup, emp="100002", start="17:00", end="18:00").status_code == 302
    error_of(book(setup, room="R-2", start="08:00", end="09:00"))
    error_of(book(setup, room="R-2", start="18:00", end="19:00"))
    error_of(book(setup, room="R-2", start="17:00", end="19:00"))


def test_開始は終了より前(setup):
    error_of(book(setup, start="10:00", end="10:00"))
    error_of(book(setup, start="11:00", end="10:00"))


def test_同じ部屋の重なりは取れない(setup):
    book(setup, start="10:00", end="12:00")
    error_of(book(setup, emp="100002", start="11:00", end="12:00"))
    error_of(book(setup, emp="100002", start="09:00", end="11:00"))
    assert len(bookings(setup)) == 1


def test_終了と開始が同じ時刻は重ならない(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, emp="100002", start="11:00", end="12:00").status_code == 302
    assert len(bookings(setup)) == 2


def test_別の部屋なら同じ時間でも取れる(setup):
    book(setup, start="10:00", end="11:00")
    assert book(setup, room="R-2", emp="100002", start="10:00", end="11:00").status_code == 302


def test_1人は同じ日に1件まで(setup):
    book(setup, start="10:00", end="11:00")
    error_of(book(setup, room="R-2", start="13:00", end="14:00"))
    assert book(setup, room="R-2", date="2026-06-16", start="13:00", end="14:00").status_code == 302


def test_取り消すと同じ日にまた取れる(setup):
    book(setup)
    assert setup.post("/seminar_rooms/cancel", data={"booking_id": "1"}).status_code == 302
    assert bookings(setup) == []
    assert book(setup, room="R-2").status_code == 302


def test_過去の日付は不可で今日はよい(setup):
    error_of(book(setup, date="2026-06-14"))
    assert book(setup, date="2026-06-15").status_code == 302


def test_今日の日付は_clock_に従う(setup, set_today):
    set_today("2026-07-01")
    error_of(book(setup, date="2026-06-30"))
    assert book(setup, date="2026-07-01").status_code == 302


def test_退職者と存在しない社員は対象にできない(setup, admin):
    admin.post("/employees/retire", data={"employee_no": "100002"})
    error_of(book(setup, emp="100002"))
    error_of(book(setup, emp="999999"))
    assert bookings(setup) == []


def test_存在しない部屋は予約できない(setup):
    error_of(book(setup, room="R-9"))


def test_部屋の番号は重複不可で名前は直せる(setup):
    error_of(setup.post("/seminar_rooms/rooms/new", data={"code": "R-1", "name": "別名"}))
    assert setup.post("/seminar_rooms/rooms/edit", data={"code": "R-1", "name": "大研修室"}).status_code == 302
    assert "大研修室" in setup.get("/seminar_rooms/").get_data(as_text=True)
    error_of(setup.post("/seminar_rooms/rooms/edit", data={"code": "R-9", "name": "x"}))


def test_存在しない予約は取り消せない(setup):
    error_of(setup.post("/seminar_rooms/cancel", data={"booking_id": "99"}))


def test_総務の担当者以外は変更できない(setup, client, make_employee):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/seminar_rooms/rooms/new", data={"code": "R-3", "name": "x"}).status_code == 403
    assert client.get("/seminar_rooms/status.json").status_code == 200


def test_操作の記録が残る(setup):
    book(setup)
    setup.post("/seminar_rooms/cancel", data={"booking_id": "1"})
    setup.post("/seminar_rooms/rooms/edit", data={"code": "R-1", "name": "新"})
    actions = [r["action"] for r in setup.get("/audit.json").get_json()["rows"] if r["module"] == "seminar_rooms"]
    assert actions == ["room_create", "room_create", "book", "cancel", "room_update"]


def test_失敗したときは記録もデータも増えない(setup):
    before = len(setup.get("/audit.json").get_json()["rows"])
    error_of(book(setup, start="09:30", end="10:30"))
    assert len(setup.get("/audit.json").get_json()["rows"]) == before


def test_日付で絞り込みと日ごとの表(setup):
    book(setup)
    book(setup, emp="100002", date="2026-06-16")
    assert "100002" not in setup.get("/seminar_rooms/?date=2026-06-15").get_data(as_text=True)
    page = setup.get("/seminar_rooms/day?date=2026-06-16").get_data(as_text=True)
    assert "100002" in page and "100001" not in page
    assert setup.get("/seminar_rooms/day?date=abc").status_code == 400

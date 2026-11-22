"""撮影スタジオの予約のテスト。総務規程の第 4・6・7 条のきまりを 1 つずつ確かめる。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def room(admin):
    admin.post("/studios/rooms/new", data={"code": "R-1", "name": "第一スタジオ"})
    return "R-1"


def book(client, employee="100001", date="2026-06-15", start="09:00", end="10:00", room_code="R-1"):
    return client.post(
        "/studios/book",
        data={"room_code": room_code, "employee_no": employee, "date": date, "start": start, "end": end},
    )


def audit_rows(app):
    with app.app_context():
        return [dict(r) for r in get_db().execute("SELECT * FROM audit_log WHERE module = 'studios' ORDER BY id")]


def bookings(client):
    return client.get("/studios/status.json").get_json()["bookings"]


def test_部屋を登録できる(admin, app):
    r = admin.post("/studios/rooms/new", data={"code": "R-1", "name": "第一"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/studios/")
    assert "第一" in admin.get("/studios/").get_data(as_text=True)
    assert audit_rows(app)[-1]["action"] == "room_create"


def test_部屋の番号は重複できない(admin, room):
    r = admin.post("/studios/rooms/new", data={"code": "R-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)


def test_部屋の名前を直せる(admin, room, app):
    r = admin.post("/studios/rooms/edit", data={"code": "R-1", "name": "新名称"})
    assert r.status_code == 302
    assert "新名称" in admin.get("/studios/").get_data(as_text=True)
    assert audit_rows(app)[-1]["action"] == "room_update"


def test_存在しない部屋は直せない(admin):
    assert admin.post("/studios/rooms/edit", data={"code": "X", "name": "n"}).status_code == 400


def test_予約できる(admin, make_employee, room, app):
    make_employee("100001")
    r = book(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/studios/")
    assert bookings(admin) == [
        {"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}
    ]
    assert audit_rows(app)[-1]["action"] == "book"


def test_60分の単位でないと予約できない(admin, make_employee, room):
    make_employee("100001")
    assert book(admin, start="09:30", end="10:30").status_code == 400
    assert book(admin, start="09:00", end="10:30").status_code == 400
    assert book(admin, start="09:00", end="10:00").status_code == 302


def test_時間帯の境界(admin, make_employee, room):
    make_employee("100001")
    make_employee("100002")
    assert book(admin, start="08:00", end="09:00").status_code == 400
    assert book(admin, start="17:00", end="19:00").status_code == 400
    assert book(admin, start="17:00", end="18:00").status_code == 302
    assert book(admin, employee="100002", date="2026-06-16", start="09:00", end="18:00").status_code == 302


def test_開始が終了以降は予約できない(admin, make_employee, room):
    make_employee("100001")
    assert book(admin, start="11:00", end="10:00").status_code == 400
    assert book(admin, start="10:00", end="10:00").status_code == 400


def test_時間が重なると予約できない(admin, make_employee, room):
    make_employee("100001")
    make_employee("100002")
    assert book(admin, start="10:00", end="12:00").status_code == 302
    r = book(admin, employee="100002", start="11:00", end="13:00")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert len(bookings(admin)) == 1


def test_終了と開始が同じ時刻は重ならない(admin, make_employee, room):
    make_employee("100001")
    make_employee("100002")
    make_employee("100003")
    assert book(admin, start="10:00", end="11:00").status_code == 302
    assert book(admin, employee="100002", start="11:00", end="12:00").status_code == 302
    assert book(admin, employee="100003", start="09:00", end="10:00").status_code == 302


def test_別の部屋や別の日は重ならない(admin, make_employee, room):
    make_employee("100001")
    make_employee("100002")
    admin.post("/studios/rooms/new", data={"code": "R-2", "name": "第二"})
    assert book(admin).status_code == 302
    assert book(admin, employee="100002", room_code="R-2").status_code == 302
    assert book(admin, employee="100002", date="2026-06-16").status_code == 302


def test_1人が同じ日に取れるのは1件まで(admin, make_employee, room):
    make_employee("100001")
    assert book(admin, start="09:00", end="10:00").status_code == 302
    assert book(admin, start="11:00", end="12:00").status_code == 400
    assert book(admin, date="2026-06-16", start="11:00", end="12:00").status_code == 302


def test_取り消すと同じ日にまた取れる(admin, make_employee, room, app):
    make_employee("100001")
    book(admin)
    r = admin.post("/studios/cancel", data={"booking_id": "1"})
    assert r.status_code == 302
    assert bookings(admin) == []
    assert audit_rows(app)[-1]["action"] == "cancel"
    assert book(admin).status_code == 302
    assert [b["id"] for b in bookings(admin)] == [2]


def test_取り消せない予約(admin, make_employee, room):
    make_employee("100001")
    book(admin)
    assert admin.post("/studios/cancel", data={"booking_id": "99"}).status_code == 400
    admin.post("/studios/cancel", data={"booking_id": "1"})
    assert admin.post("/studios/cancel", data={"booking_id": "1"}).status_code == 400


def test_過去の日付は予約できず今日はよい(admin, make_employee, room):
    make_employee("100001")
    assert book(admin, date="2026-06-14").status_code == 400
    assert book(admin, date="2026-06-15").status_code == 302


def test_今日の日付はclockに従う(admin, make_employee, room, set_today):
    make_employee("100001")
    set_today("2026-07-01")
    assert book(admin, date="2026-06-30").status_code == 400
    assert book(admin, date="2026-07-01").status_code == 302


def test_退職した社員と存在しない社員は予約できない(admin, make_employee, room):
    make_employee("100001")
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert book(admin).status_code == 400
    assert book(admin, employee="999999").status_code == 400


def test_存在しない部屋と不正な日時は400(admin, make_employee, room):
    make_employee("100001")
    assert book(admin, room_code="X").status_code == 400
    assert book(admin, date="2026/06/15").status_code == 400
    assert book(admin, start="9時", end="10:00").status_code == 400
    assert bookings(admin) == []


def test_担当者でないと操作できない(client, admin, make_employee, room):
    make_employee("100001", role="employee")
    admin.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert book(client).status_code == 403
    assert client.post("/studios/rooms/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert client.post("/studios/cancel", data={"booking_id": "1"}).status_code == 403
    assert client.get("/studios/status.json").status_code == 200


def test_その日の表と日付の絞り込み(admin, make_employee, room):
    make_employee("100001")
    make_employee("100002")
    book(admin)
    book(admin, employee="100002", date="2026-06-16")
    day = admin.get("/studios/day?date=2026-06-15").get_data(as_text=True)
    assert "09:00-10:00" in day and "100002" not in day
    assert admin.get("/studios/day").status_code == 400
    listing = admin.get("/studios/?date=2026-06-16").get_data(as_text=True)
    assert "100002" in listing and "100001" not in listing


def test_ログインしていないと見られない(client):
    assert client.get("/studios/status.json").status_code == 302

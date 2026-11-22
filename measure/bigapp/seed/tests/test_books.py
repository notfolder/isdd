"""書籍の貸出のテスト。きまりを 1 つずつ確かめる。今日は conftest の 2026-06-15。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def staff(admin):
    return admin


def add(c, code, name="本"):
    return c.post("/books/items/new", data={"code": code, "name": name})


def lend(c, code, no, lent_on=None):
    data = {"item_code": code, "employee_no": no}
    if lent_on:
        data["lent_on"] = lent_on
    return c.post("/books/lend", data=data)


def status(c):
    return {i["code"]: i for i in c.get("/books/status.json").get_json()["items"]}


def test_register_and_list(staff):
    r = add(staff, "A-1", "吾輩は猫である")
    assert r.status_code == 302 and r.headers["Location"].endswith("/books/")
    page = staff.get("/books/").get_data(as_text=True)
    assert "A-1" in page and "吾輩は猫である" in page


def test_duplicate_code_rejected(staff):
    add(staff, "A-1")
    r = add(staff, "A-1", "別の本")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert len(status(staff)) == 1


def test_non_staff_cannot_post(client, admin, make_employee):
    make_employee("100001")
    admin.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert add(client, "A-1").status_code == 403
    assert client.get("/books/status.json").status_code == 200


def test_lend_sets_due_21_days(staff, make_employee):
    make_employee("100001")
    add(staff, "A-1")
    assert lend(staff, "A-1", "100001").status_code == 302
    item = status(staff)["A-1"]
    assert item["status"] == "lent" and item["borrower"] == "100001"
    assert item["lent_on"] == "2026-06-15" and item["due_on"] == "2026-07-06"


def test_lend_with_date_and_future_date(staff, make_employee):
    make_employee("100001")
    add(staff, "A-1")
    assert lend(staff, "A-1", "100001", "2026-06-16").status_code == 400  # 明日は不可
    assert lend(staff, "A-1", "100001", "2026-06-15").status_code == 302  # 今日は可
    add(staff, "A-2")
    assert lend(staff, "A-2", "100001", "2026-06-01").status_code == 302
    assert status(staff)["A-2"]["due_on"] == "2026-06-22"


def test_invalid_date_rejected(staff, make_employee):
    make_employee("100001")
    add(staff, "A-1")
    assert lend(staff, "A-1", "100001", "2026/06/01").status_code == 400
    assert status(staff)["A-1"]["status"] == "free"


def test_limit_three_loans(staff, make_employee):
    make_employee("100001")
    for i in range(1, 5):
        add(staff, f"A-{i}")
    for i in range(1, 4):
        assert lend(staff, f"A-{i}", "100001").status_code == 302
    r = lend(staff, "A-4", "100001")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    staff.post("/books/return", data={"item_code": "A-1"})
    assert lend(staff, "A-4", "100001").status_code == 302


def test_cannot_lend_lent_item(staff, make_employee):
    make_employee("100001")
    make_employee("100002")
    add(staff, "A-1")
    lend(staff, "A-1", "100001")
    assert lend(staff, "A-1", "100002").status_code == 400
    assert status(staff)["A-1"]["borrower"] == "100001"


def test_overdue_boundary(staff, make_employee, set_today):
    make_employee("100001")
    add(staff, "A-1")
    add(staff, "A-2")
    lend(staff, "A-1", "100001")  # 期限 2026-07-06
    set_today("2026-07-06")  # 期限当日は延滞でない
    assert status(staff)["A-1"]["status"] == "lent"
    assert lend(staff, "A-2", "100001").status_code == 302
    set_today("2026-07-07")  # 翌日から延滞
    assert status(staff)["A-1"]["status"] == "overdue"


def test_delinquent_borrower_cannot_borrow(staff, make_employee, set_today):
    make_employee("100001")
    make_employee("100002")
    add(staff, "A-1")
    add(staff, "A-2")
    lend(staff, "A-1", "100001")
    set_today("2026-07-07")
    r = lend(staff, "A-2", "100001")
    assert r.status_code == 400
    assert lend(staff, "A-2", "100002").status_code == 302  # 他の社員は借りられる
    staff.post("/books/return", data={"item_code": "A-1"})
    assert lend(staff, "A-2", "100001").status_code == 400  # A-2 は貸出中
    add(staff, "A-3")
    assert lend(staff, "A-3", "100001").status_code == 302  # 返却すれば借りられる


def test_return_keeps_history(staff, make_employee):
    make_employee("100001")
    add(staff, "A-1", "歴史の本")
    lend(staff, "A-1", "100001")
    assert staff.post("/books/return", data={"item_code": "A-1"}).status_code == 302
    assert status(staff)["A-1"]["status"] == "free"
    assert "歴史の本" in staff.get("/books/history").get_data(as_text=True)
    assert staff.post("/books/return", data={"item_code": "A-1"}).status_code == 400


def test_delete_rules(staff, make_employee):
    make_employee("100001")
    add(staff, "A-1")
    lend(staff, "A-1", "100001")
    assert staff.post("/books/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(staff)
    staff.post("/books/return", data={"item_code": "A-1"})
    assert staff.post("/books/items/delete", data={"code": "A-1"}).status_code == 302
    assert "A-1" not in status(staff)
    assert staff.post("/books/items/delete", data={"code": "A-1"}).status_code == 400


def test_edit_name(staff):
    add(staff, "A-1", "旧")
    assert staff.post("/books/items/edit", data={"code": "A-1", "name": "新"}).status_code == 302
    assert status(staff)["A-1"]["name"] == "新"
    assert staff.post("/books/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400


def test_retired_and_unknown_employee_rejected(staff, make_employee):
    make_employee("100001")
    staff.post("/employees/retire", data={"employee_no": "100001"})
    add(staff, "A-1")
    assert lend(staff, "A-1", "100001").status_code == 400
    assert lend(staff, "A-1", "999999").status_code == 400
    assert status(staff)["A-1"]["status"] == "free"


def test_search_filters(staff):
    add(staff, "A-1", "料理の本")
    add(staff, "B-2", "旅行記")
    page = staff.get("/books/?q=旅行").get_data(as_text=True)
    assert "B-2" in page and "A-1" not in page
    page = staff.get("/books/?q=A-").get_data(as_text=True)
    assert "A-1" in page and "B-2" not in page


def test_status_json_sorted_and_audit(staff, make_employee, app):
    make_employee("100001")
    add(staff, "B-1")
    add(staff, "A-1")
    lend(staff, "A-1", "100001")
    staff.post("/books/return", data={"item_code": "A-1"})
    assert list(status(staff)) == ["A-1", "B-1"]
    rows = staff.get("/audit.json").get_json()["rows"]
    actions = [r["action"] for r in rows if r["module"] == "books"]
    assert actions == ["item_create", "item_create", "lend", "return"]


def test_rejected_operation_not_audited(staff):
    add(staff, "A-1")
    add(staff, "A-1")
    rows = staff.get("/audit.json").get_json()["rows"]
    assert len([r for r in rows if r["module"] == "books"]) == 1

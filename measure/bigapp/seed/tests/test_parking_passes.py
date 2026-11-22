"""駐車許可証の貸出のテスト。"""

import pytest


def add_item(admin, code="A-1", name="第一駐車場"):
    return admin.post("/parking_passes/items/new", data={"code": code, "name": name})


def lend(admin, code="A-1", no="100001", lent_on=None):
    data = {"item_code": code, "employee_no": no}
    if lent_on:
        data["lent_on"] = lent_on
    return admin.post("/parking_passes/lend", data=data)


def status(admin):
    return {i["code"]: i for i in admin.get("/parking_passes/status.json").get_json()["items"]}


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    add_item(admin)
    add_item(admin, "A-2", "第二駐車場")
    return admin


def test_register_and_list(setup):
    items = status(setup)
    assert items["A-1"] == {"code": "A-1", "name": "第一駐車場", "status": "free", "borrower": None, "lent_on": None, "due_on": None}
    assert list(items) == ["A-1", "A-2"]
    assert "第一駐車場" in setup.get("/parking_passes/").get_data(as_text=True)


def test_duplicate_code_rejected(setup):
    r = add_item(setup)
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_search(setup):
    assert "第二" not in setup.get("/parking_passes/?q=A-1").get_data(as_text=True)
    assert "第二" in setup.get("/parking_passes/?q=第二").get_data(as_text=True)


def test_edit_name(setup):
    r = setup.post("/parking_passes/items/edit", data={"code": "A-1", "name": "新名称"})
    assert r.status_code == 302 and status(setup)["A-1"]["name"] == "新名称"
    assert setup.post("/parking_passes/items/edit", data={"code": "ZZ", "name": "x"}).status_code == 400


def test_lend_defaults_to_today_and_due_30_days(setup):
    r = lend(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/parking_passes/")
    item = status(setup)["A-1"]
    assert (item["status"], item["borrower"], item["lent_on"], item["due_on"]) == ("lent", "100001", "2026-06-15", "2026-07-15")


def test_lend_with_date_and_future_rejected(setup):
    assert lend(setup, lent_on="2026-06-01").status_code == 302
    assert status(setup)["A-1"]["due_on"] == "2026-07-01"
    r = lend(setup, "A-2", "100002", "2026-06-16")
    assert r.status_code == 400 and status(setup)["A-2"]["status"] == "free"
    assert lend(setup, "A-2", "100002", "2026-06-15").status_code == 302  # 今日は可


def test_one_item_per_person(setup):
    lend(setup)
    assert lend(setup, "A-2", "100001").status_code == 400
    assert status(setup)["A-2"]["status"] == "free"


def test_item_already_lent(setup):
    lend(setup)
    assert lend(setup, "A-1", "100002").status_code == 400


def test_retired_and_unknown_employee_rejected(setup, make_employee):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", "100002").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400
    assert lend(setup, "ZZ", "100001").status_code == 400


def test_overdue_boundary(setup, set_today):
    lend(setup, lent_on="2026-06-15")  # 期限 2026-07-15
    set_today("2026-07-15")
    assert status(setup)["A-1"]["status"] == "lent"  # 期限日当日は延滞ではない
    set_today("2026-07-16")
    assert status(setup)["A-1"]["status"] == "overdue"


def test_overdue_borrower_cannot_borrow_again_but_returns_then_can(setup, set_today):
    lend(setup)
    set_today("2026-07-16")
    r = lend(setup, "A-2", "100001")
    assert r.status_code == 400 and "期限" in r.get_data(as_text=True)
    assert setup.post("/parking_passes/return", data={"item_code": "A-1"}).status_code == 302
    assert lend(setup, "A-2", "100001").status_code == 302


def test_return_and_history(setup, set_today):
    lend(setup)
    set_today("2026-06-20")
    assert setup.post("/parking_passes/return", data={"item_code": "A-1"}).status_code == 302
    assert status(setup)["A-1"]["status"] == "free"
    html = setup.get("/parking_passes/history").get_data(as_text=True)
    assert "A-1" in html and "2026-06-20" in html
    assert setup.post("/parking_passes/return", data={"item_code": "A-1"}).status_code == 400


def test_delete_rules(setup):
    lend(setup)
    assert setup.post("/parking_passes/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(setup)
    assert setup.post("/parking_passes/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(setup)


def test_staff_only_for_changes(client, setup, make_employee):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/parking_passes/items/new", data={"code": "B", "name": "x"}).status_code == 403
    assert lend(client, "A-1", "100001").status_code == 403
    assert client.get("/parking_passes/status.json").status_code == 200


def test_audit_records(setup):
    lend(setup)
    setup.post("/parking_passes/return", data={"item_code": "A-1"})
    setup.post("/parking_passes/items/edit", data={"code": "A-2", "name": "改"})
    setup.post("/parking_passes/items/delete", data={"code": "A-2"})
    rows = [(r["action"], r["target"]) for r in setup.get("/audit.json").get_json()["rows"] if r["module"] == "parking_passes"]
    assert rows == [("item_create", "A-1"), ("item_create", "A-2"), ("lend", "A-1"), ("return", "A-1"), ("item_update", "A-2"), ("item_delete", "A-2")]

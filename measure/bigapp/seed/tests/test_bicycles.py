"""社用自転車の貸出のテスト。"""

import pytest


@pytest.fixture
def bike(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/bicycles/items/new", data={"code": "A-1", "name": "赤"})
    admin.post("/bicycles/items/new", data={"code": "A-2", "name": "青"})
    return admin


def status(client):
    return {i["code"]: i for i in client.get("/bicycles/status.json").get_json()["items"]}


def audit_rows(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "bicycles"]


def lend(client, code="A-1", no="100001", **extra):
    return client.post("/bicycles/lend", data={"item_code": code, "employee_no": no, **extra})


def test_register_item_and_audit(admin):
    r = admin.post("/bicycles/items/new", data={"code": "A-1", "name": "赤"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/bicycles/")
    assert status(admin)["A-1"]["name"] == "赤"
    assert audit_rows(admin) == [("bicycles", "item_create", "A-1")]


def test_duplicate_code_rejected(bike):
    r = bike.post("/bicycles/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert status(bike)["A-1"]["name"] == "赤"


def test_edit_and_delete_item(bike):
    assert bike.post("/bicycles/items/edit", data={"code": "A-1", "name": "新"}).status_code == 302
    assert status(bike)["A-1"]["name"] == "新"
    assert bike.post("/bicycles/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(bike)
    assert ("bicycles", "item_update", "A-1") in audit_rows(bike)
    assert ("bicycles", "item_delete", "A-2") in audit_rows(bike)


def test_edit_unknown_item_rejected(bike):
    assert bike.post("/bicycles/items/edit", data={"code": "Z", "name": "x"}).status_code == 400


def test_lend_sets_due_one_day_later(bike):
    assert lend(bike).status_code == 302
    s = status(bike)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-16")
    assert ("bicycles", "lend", "A-1") in audit_rows(bike)


def test_lend_with_past_date_and_overdue_status(bike):
    assert lend(bike, lent_on="2026-06-14").status_code == 302
    s = status(bike)["A-1"]
    assert s["due_on"] == "2026-06-15" and s["status"] == "lent"  # 期限の当日は延滞ではない


def test_overdue_when_today_after_due(bike, set_today):
    lend(bike)
    set_today("2026-06-16")
    assert status(bike)["A-1"]["status"] == "lent"
    set_today("2026-06-17")
    assert status(bike)["A-1"]["status"] == "overdue"


def test_future_lent_on_rejected_but_today_ok(bike):
    assert lend(bike, lent_on="2026-06-16").status_code == 400
    assert lend(bike, lent_on="2026-06-15").status_code == 302


def test_bad_date_format_rejected(bike):
    assert lend(bike, lent_on="2026/06/15").status_code == 400
    assert status(bike)["A-1"]["status"] == "free"


def test_item_already_lent_rejected(bike):
    lend(bike)
    r = lend(bike, no="100002")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)


def test_one_item_per_employee(bike):
    lend(bike)
    assert lend(bike, code="A-2").status_code == 400
    assert status(bike)["A-2"]["status"] == "free"


def test_overdue_holder_cannot_borrow_new(bike, set_today):
    lend(bike)
    set_today("2026-06-17")
    r = lend(bike, code="A-2")
    assert r.status_code == 400 and "期限" in r.get_data(as_text=True)


def test_overdue_holder_blocked_but_others_can_borrow(bike, set_today):
    lend(bike)
    set_today("2026-06-17")
    assert lend(bike, code="A-2", no="100002").status_code == 302


def test_after_return_can_borrow_again(bike, set_today):
    lend(bike)
    set_today("2026-06-17")
    assert bike.post("/bicycles/return", data={"item_code": "A-1"}).status_code == 302
    assert lend(bike, code="A-2").status_code == 302


def test_retired_and_unknown_employee_rejected(bike):
    bike.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(bike, no="100002").status_code == 400
    assert lend(bike, no="999999").status_code == 400
    assert status(bike)["A-1"]["status"] == "free"


def test_cannot_delete_lent_item(bike):
    lend(bike)
    assert bike.post("/bicycles/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(bike)


def test_return_records_history_newest_first(bike, set_today):
    lend(bike)
    bike.post("/bicycles/return", data={"item_code": "A-1"})
    set_today("2026-06-16")
    lend(bike, code="A-2", no="100002")
    bike.post("/bicycles/return", data={"item_code": "A-2"})
    html = bike.get("/bicycles/history").get_data(as_text=True)
    assert html.index("A-2") < html.index("A-1")
    assert ("bicycles", "return", "A-1") in audit_rows(bike)


def test_return_when_not_lent_rejected(bike):
    assert bike.post("/bicycles/return", data={"item_code": "A-1"}).status_code == 400


def test_search_filter(bike):
    html = bike.get("/bicycles/?q=青").get_data(as_text=True)
    assert "A-2" in html and "A-1" not in html


def test_status_json_sorted_and_free_shape(bike):
    items = bike.get("/bicycles/status.json").get_json()["items"]
    assert [i["code"] for i in items] == ["A-1", "A-2"]
    assert items[0] == {"code": "A-1", "name": "赤", "status": "free", "borrower": None, "lent_on": None, "due_on": None}


def test_employee_cannot_change_but_can_read(app, make_employee, client):
    make_employee("100001", "山田")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/bicycles/items/new", data={"code": "B", "name": "x"}).status_code == 403
    assert client.get("/bicycles/status.json").status_code == 200
    assert client.get("/bicycles/").status_code == 200


def test_rejected_operation_leaves_no_audit(bike):
    before = audit_rows(bike)
    lend(bike, no="999999")
    assert audit_rows(bike) == before

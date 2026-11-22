"""社用車の貸出のテスト。今日は 2026-06-15（conftest）。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    make_employee("100003", "鈴木", role="staff")
    admin.post("/vehicles/items/new", data={"code": "A-1", "name": "軽自動車"})
    admin.post("/vehicles/items/new", data={"code": "A-2", "name": "ワゴン"})
    return admin


def status(client):
    return {i["code"]: i for i in client.get("/vehicles/status.json").get_json()["items"]}


def audit_rows(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "vehicles"]


def test_register_item_and_list(setup):
    assert status(setup)["A-1"]["status"] == "free"
    html = setup.get("/vehicles/").get_data(as_text=True)
    assert "A-1" in html and "軽自動車" in html
    assert ("vehicles", "item_create", "A-1") in audit_rows(setup)


def test_duplicate_code_rejected(setup):
    r = setup.post("/vehicles/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert status(setup)["A-1"]["name"] == "軽自動車"


def test_edit_item_name(setup):
    assert setup.post("/vehicles/items/edit", data={"code": "A-1", "name": "新車"}).status_code == 302
    assert status(setup)["A-1"]["name"] == "新車"
    assert setup.post("/vehicles/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400
    assert ("vehicles", "item_update", "A-1") in audit_rows(setup)


def test_lend_sets_due_three_days_later(setup):
    r = setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/vehicles/")
    s = status(setup)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-18")
    assert ("vehicles", "lend", "A-1:100001") in audit_rows(setup)


def test_lend_with_explicit_date_and_future_rejected(setup):
    assert setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001", "lent_on": "2026-06-15"}).status_code == 302
    assert setup.post("/vehicles/lend", data={"item_code": "A-2", "employee_no": "100002", "lent_on": "2026-06-16"}).status_code == 400
    assert status(setup)["A-2"]["status"] == "free"
    assert setup.post("/vehicles/lend", data={"item_code": "A-2", "employee_no": "100002", "lent_on": "abc"}).status_code == 400


def test_lent_item_cannot_be_lent_again(setup):
    setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    assert setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100002"}).status_code == 400
    assert status(setup)["A-1"]["borrower"] == "100001"


def test_one_item_per_person(setup):
    setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    r = setup.post("/vehicles/lend", data={"item_code": "A-2", "employee_no": "100001"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert status(setup)["A-2"]["status"] == "free"


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100002"}).status_code == 400
    assert setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "999999"}).status_code == 400
    assert status(setup)["A-1"]["status"] == "free"


def test_status_due_day_is_still_lent_next_day_is_overdue(setup, set_today):
    setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    set_today("2026-06-18")  # 期限の当日
    assert status(setup)["A-1"]["status"] == "lent"
    set_today("2026-06-19")  # 期限の翌日
    assert status(setup)["A-1"]["status"] == "overdue"


def test_return_frees_item_and_keeps_history(setup):
    setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    assert setup.post("/vehicles/return", data={"item_code": "A-1"}).status_code == 302
    s = status(setup)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("free", None, None, None)
    assert "100001" in setup.get("/vehicles/history").get_data(as_text=True)
    assert ("vehicles", "return", "A-1:100001") in audit_rows(setup)
    # 返却すれば同じ人がまた借りられる
    assert setup.post("/vehicles/lend", data={"item_code": "A-2", "employee_no": "100001"}).status_code == 302


def test_return_of_free_item_rejected(setup):
    assert setup.post("/vehicles/return", data={"item_code": "A-1"}).status_code == 400


def test_delete_item_rules(setup):
    setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    assert setup.post("/vehicles/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(setup)
    assert setup.post("/vehicles/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(setup)
    assert ("vehicles", "item_delete", "A-2") in audit_rows(setup)


def test_past_due_holder_cannot_borrow_new_item(setup, set_today):
    setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    set_today("2026-06-19")
    r = setup.post("/vehicles/lend", data={"item_code": "A-2", "employee_no": "100001"})
    assert r.status_code == 400 and "期限" in r.get_data(as_text=True)


def test_other_person_can_borrow_other_item_when_someone_is_past_due(setup, set_today):
    setup.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"})
    set_today("2026-06-19")
    assert setup.post("/vehicles/lend", data={"item_code": "A-2", "employee_no": "100002"}).status_code == 302


def test_search_filters_list(setup):
    html = setup.get("/vehicles/?q=ワゴン").get_data(as_text=True)
    assert "A-2" in html and "A-1" not in html
    assert "A-1" in setup.get("/vehicles/?q=A-").get_data(as_text=True)


def test_status_json_sorted_by_code(setup):
    assert [i["code"] for i in setup.get("/vehicles/status.json").get_json()["items"]] == ["A-1", "A-2"]


def test_non_staff_cannot_change_but_can_view(client, setup):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/vehicles/lend", data={"item_code": "A-1", "employee_no": "100001"}).status_code == 403
    assert client.post("/vehicles/items/new", data={"code": "B", "name": "b"}).status_code == 403
    assert client.get("/vehicles/status.json").status_code == 200
    assert client.get("/vehicles/").status_code == 200

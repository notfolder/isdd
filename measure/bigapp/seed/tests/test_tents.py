"""テントの貸出のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/tents/items/new", data={"code": "A-1", "name": "4 人用"})
    admin.post("/tents/items/new", data={"code": "A-2", "name": "6 人用"})
    return admin


def status(c):
    return {i["code"]: i for i in c.get("/tents/status.json").get_json()["items"]}


def audit_rows(c):
    return [(r["module"], r["action"], r["target"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "tents"]


def lend(c, item="A-1", emp="100001", **kw):
    return c.post("/tents/lend", data={"item_code": item, "employee_no": emp, **kw})


def test_create_item_and_duplicate(setup):
    assert [i["code"] for i in status(setup).values()] == ["A-1", "A-2"]
    r = setup.post("/tents/items/new", data={"code": "A-1", "name": "x"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert len(status(setup)) == 2


def test_update_and_delete_item(setup):
    assert setup.post("/tents/items/edit", data={"code": "A-1", "name": "新"}).status_code == 302
    assert status(setup)["A-1"]["name"] == "新"
    assert setup.post("/tents/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(setup)
    assert setup.post("/tents/items/delete", data={"code": "Z"}).status_code == 400


def test_lend_sets_due_four_days(setup):
    r = lend(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/tents/")
    i = status(setup)["A-1"]
    assert (i["status"], i["borrower"], i["lent_on"], i["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-19")


def test_lend_with_date(setup):
    lend(setup, lent_on="2026-06-10")
    assert status(setup)["A-1"]["due_on"] == "2026-06-14"


def test_future_date_rejected(setup):
    assert lend(setup, lent_on="2026-06-16").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"
    assert lend(setup, lent_on="2026-06-15").status_code == 302


def test_one_item_per_person(setup):
    lend(setup)
    assert lend(setup, item="A-2").status_code == 400
    assert status(setup)["A-2"]["status"] == "free"


def test_lent_item_cannot_be_lent_or_deleted(setup):
    lend(setup)
    assert lend(setup, emp="100002").status_code == 400
    assert setup.post("/tents/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(setup)


def test_retired_and_unknown_employee(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, emp="100002").status_code == 400
    assert lend(setup, emp="999999").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"


def test_overdue_boundary(setup, set_today):
    lend(setup)  # 期限 6/19
    set_today("2026-06-19")
    assert status(setup)["A-1"]["status"] == "lent"
    set_today("2026-06-20")
    assert status(setup)["A-1"]["status"] == "overdue"


def test_delinquent_cannot_borrow_again(setup, set_today):
    lend(setup)
    set_today("2026-06-20")
    assert lend(setup, item="A-2").status_code == 400


def test_return_and_history(setup):
    lend(setup)
    assert setup.post("/tents/return", data={"item_code": "A-1"}).status_code == 302
    assert status(setup)["A-1"]["status"] == "free"
    assert "100001" in setup.get("/tents/history").get_data(as_text=True)
    assert setup.post("/tents/return", data={"item_code": "A-1"}).status_code == 400
    assert lend(setup, item="A-2").status_code == 302  # 返却後は再び借りられる


def test_return_after_overdue_allows_new_loan(setup, set_today):
    lend(setup)
    set_today("2026-06-30")
    setup.post("/tents/return", data={"item_code": "A-1"})
    assert lend(setup, item="A-2").status_code == 302


def test_search(setup):
    html = setup.get("/tents/?q=6 人").get_data(as_text=True)
    assert "A-2" in html and "A-1" not in html


def test_staff_only(client, setup, make_employee):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/tents/items/new", data={"code": "B", "name": "x"}).status_code == 403
    assert lend(client).status_code == 403
    assert client.get("/tents/status.json").status_code == 200


def test_audit_trail(setup):
    lend(setup)
    lend(setup, emp="100002")  # 失敗は残さない
    setup.post("/tents/return", data={"item_code": "A-1"})
    assert audit_rows(setup) == [
        ("tents", "item_create", "A-1"), ("tents", "item_create", "A-2"), ("tents", "lend", "A-1"), ("tents", "return", "A-1")]

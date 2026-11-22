"""台車の貸出のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    for code in ("A-1", "A-2", "A-3"):
        assert admin.post("/carts/items/new", data={"code": code, "name": "台車" + code}).status_code == 302
    return admin


def lend(c, item, emp, on=None):
    data = {"item_code": item, "employee_no": emp}
    if on:
        data["lent_on"] = on
    return c.post("/carts/lend", data=data)


def items(c):
    return {i["code"]: i for i in c.get("/carts/status.json").get_json()["items"]}


def audit_actions(c):
    return [(r["module"], r["action"], r["target"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "carts"]


def test_item_create_edit_delete_and_audit(setup):
    c = setup
    assert c.post("/carts/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert items(c)["A-1"]["name"] == "新名"
    assert c.post("/carts/items/delete", data={"code": "A-3"}).status_code == 302
    assert "A-3" not in items(c)
    assert audit_actions(c)[-2:] == [("carts", "item_update", "A-1"), ("carts", "item_delete", "A-3")]


def test_duplicate_code_rejected(setup):
    r = setup.post("/carts/items/new", data={"code": "A-1", "name": "重複"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)


def test_edit_delete_missing_item_rejected(setup):
    assert setup.post("/carts/items/edit", data={"code": "Z", "name": "x"}).status_code == 400
    assert setup.post("/carts/items/delete", data={"code": "Z"}).status_code == 400


def test_lend_sets_due_one_day_and_audit(setup):
    assert lend(setup, "A-1", "100001").status_code == 302
    i = items(setup)["A-1"]
    assert (i["status"], i["borrower"], i["lent_on"], i["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-16")
    assert audit_actions(setup)[-1] == ("carts", "lend", "A-1")


def test_lend_with_past_date(setup):
    assert lend(setup, "A-1", "100001", "2026-06-14").status_code == 302
    assert items(setup)["A-1"]["due_on"] == "2026-06-15"


def test_future_date_rejected_today_ok(setup):
    assert lend(setup, "A-1", "100001", "2026-06-16").status_code == 400
    assert lend(setup, "A-1", "100001", "2026-06-15").status_code == 302


def test_bad_date_rejected(setup):
    assert lend(setup, "A-1", "100001", "2026/06/15").status_code == 400


def test_limit_two_per_person(setup):
    assert lend(setup, "A-1", "100001").status_code == 302
    assert lend(setup, "A-2", "100001").status_code == 302
    r = lend(setup, "A-3", "100001")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert items(setup)["A-3"]["status"] == "free"


def test_cannot_lend_item_in_use(setup):
    lend(setup, "A-1", "100001")
    assert lend(setup, "A-1", "100002").status_code == 400


def test_due_day_is_not_overdue_boundary(setup, set_today):
    lend(setup, "A-1", "100001")  # 期限 06-16
    set_today("2026-06-16")
    assert items(setup)["A-1"]["status"] == "lent"
    assert lend(setup, "A-2", "100001").status_code == 302


def test_overdue_blocks_new_lending(setup, set_today):
    lend(setup, "A-1", "100001")
    set_today("2026-06-17")
    assert items(setup)["A-1"]["status"] == "overdue"
    assert lend(setup, "A-2", "100001").status_code == 400
    assert lend(setup, "A-2", "100002").status_code == 302


def test_return_frees_item_and_keeps_history(setup, set_today):
    lend(setup, "A-1", "100001")
    set_today("2026-06-16")
    assert setup.post("/carts/return", data={"item_code": "A-1"}).status_code == 302
    assert items(setup)["A-1"]["status"] == "free"
    page = setup.get("/carts/history").get_data(as_text=True)
    assert "A-1" in page and "100001" in page and "2026-06-16" in page
    assert audit_actions(setup)[-1] == ("carts", "return", "A-1")
    assert lend(setup, "A-1", "100002").status_code == 302


def test_return_not_lent_rejected(setup):
    assert setup.post("/carts/return", data={"item_code": "A-1"}).status_code == 400


def test_cannot_delete_item_in_use(setup):
    lend(setup, "A-1", "100001")
    assert setup.post("/carts/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(setup)


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", "100002").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400
    assert items(setup)["A-1"]["status"] == "free"


def test_rejection_leaves_no_audit(setup):
    before = len(audit_actions(setup))
    lend(setup, "A-1", "999999")
    assert len(audit_actions(setup)) == before


def test_employee_cannot_post_but_can_view(setup, client):
    from app.core.db import ADMIN_NO  # noqa: F401
    setup.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/carts/items/new", data={"code": "B", "name": "x"}).status_code == 403
    assert client.get("/carts/").status_code == 200
    assert client.get("/carts/status.json").status_code == 200


def test_search_and_status_order(setup):
    page = setup.get("/carts/?q=A-2").get_data(as_text=True)
    assert "A-2" in page and "A-3" not in page
    assert list(items(setup)) == ["A-1", "A-2", "A-3"]

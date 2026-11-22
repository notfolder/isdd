"""備品の貸出のテスト。きまりを 1 つずつ確かめる。今日は 2026-06-15（conftest）。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    for code in ("A-1", "A-2", "A-3"):
        assert admin.post("/equipment/items/new", data={"code": code, "name": f"備品{code}"}).status_code == 302
    return admin


def lend(c, code, no="100001", **extra):
    return c.post("/equipment/lend", data={"item_code": code, "employee_no": no, **extra})


def items(c):
    return {i["code"]: i for i in c.get("/equipment/status.json").get_json()["items"]}


def audit_actions(c):
    return [(r["module"], r["action"], r["target"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "equipment"]


def test_lend_default_date_and_due_14_days(setup):
    r = lend(setup, "A-1")
    assert r.status_code == 302 and r.headers["Location"].endswith("/equipment/")
    it = items(setup)["A-1"]
    assert (it["status"], it["borrower"], it["lent_on"], it["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-29")


def test_lend_with_explicit_past_date(setup):
    lend(setup, "A-1", lent_on="2026-06-01")
    assert items(setup)["A-1"]["due_on"] == "2026-06-15"


def test_future_date_rejected_and_today_accepted(setup):
    r = lend(setup, "A-1", lent_on="2026-06-16")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert items(setup)["A-1"]["status"] == "free"
    assert lend(setup, "A-1", lent_on="2026-06-15").status_code == 302


def test_invalid_date_rejected(setup):
    assert lend(setup, "A-1", lent_on="abc").status_code == 400


def test_third_loan_rejected_second_accepted(setup):
    assert lend(setup, "A-1").status_code == 302
    assert lend(setup, "A-2").status_code == 302
    r = lend(setup, "A-3")
    assert r.status_code == 400
    assert items(setup)["A-3"]["status"] == "free"
    assert lend(setup, "A-3", no="100002").status_code == 302


def test_cannot_lend_item_already_lent(setup):
    lend(setup, "A-1")
    assert lend(setup, "A-1", no="100002").status_code == 400
    assert items(setup)["A-1"]["borrower"] == "100001"


def test_overdue_boundary(setup, set_today):
    lend(setup, "A-1")  # 期限 2026-06-29
    set_today("2026-06-29")  # 期限当日は延滞ではない
    assert items(setup)["A-1"]["status"] == "lent"
    assert lend(setup, "A-2").status_code == 302
    set_today("2026-06-30")
    assert items(setup)["A-1"]["status"] == "overdue"


def test_overdue_holder_cannot_borrow(setup, set_today):
    lend(setup, "A-1")
    set_today("2026-06-30")
    r = lend(setup, "A-2")
    assert r.status_code == 400
    assert lend(setup, "A-2", no="100002").status_code == 302  # 他の社員は借りられる


def test_return_frees_item_and_keeps_history(setup):
    lend(setup, "A-1")
    r = setup.post("/equipment/return", data={"item_code": "A-1"})
    assert r.status_code == 302
    assert items(setup)["A-1"]["status"] == "free"
    html = setup.get("/equipment/history").get_data(as_text=True)
    assert "A-1" in html and "2026-06-29" in html


def test_return_clears_overdue_block(setup, set_today):
    lend(setup, "A-1")
    set_today("2026-06-30")
    setup.post("/equipment/return", data={"item_code": "A-1"})
    assert lend(setup, "A-2").status_code == 302


def test_return_of_free_item_rejected(setup):
    assert setup.post("/equipment/return", data={"item_code": "A-1"}).status_code == 400


def test_retired_and_unknown_employee_rejected(setup, make_employee):
    make_employee("100003", "退職者")
    setup.post("/employees/retire", data={"employee_no": "100003"})
    assert lend(setup, "A-1", no="100003").status_code == 400
    assert lend(setup, "A-1", no="999999").status_code == 400
    assert lend(setup, "ZZZ").status_code == 400


def test_duplicate_code_rejected(setup):
    r = setup.post("/equipment/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)


def test_edit_name(setup):
    assert setup.post("/equipment/items/edit", data={"code": "A-1", "name": "新しい名前"}).status_code == 302
    assert items(setup)["A-1"]["name"] == "新しい名前"
    assert setup.post("/equipment/items/edit", data={"code": "NONE", "name": "x"}).status_code == 400


def test_delete_item_and_lent_item_protected(setup):
    lend(setup, "A-1")
    assert setup.post("/equipment/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(setup)
    assert setup.post("/equipment/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in items(setup)


def test_non_staff_cannot_post_but_can_read(setup, client, make_employee):
    setup.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/equipment/items/new", data={"code": "B", "name": "b"}).status_code == 403
    assert client.post("/equipment/lend", data={"item_code": "A-1", "employee_no": "100001"}).status_code == 403
    assert client.get("/equipment/").status_code == 200
    assert client.get("/equipment/status.json").status_code == 200


def test_search_filter(setup):
    html = setup.get("/equipment/?q=A-2").get_data(as_text=True)
    assert "A-2" in html and "A-1" not in html


def test_status_json_sorted_and_audit(setup):
    lend(setup, "A-2")
    setup.post("/equipment/return", data={"item_code": "A-2"})
    assert list(items(setup)) == ["A-1", "A-2", "A-3"]
    assert items(setup)["A-3"]["borrower"] is None
    actions = audit_actions(setup)
    assert ("equipment", "lend", "A-2") in actions and ("equipment", "return", "A-2") in actions
    assert ("equipment", "item_create", "A-1") in actions


def test_rejected_operation_not_audited(setup):
    before = len(audit_actions(setup))
    lend(setup, "A-1", lent_on="2030-01-01")
    assert len(audit_actions(setup)) == before

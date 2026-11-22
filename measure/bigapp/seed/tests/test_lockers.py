"""ロッカーの貸与のテスト。"""

import pytest


def add_item(admin, code="A-1", name="ロッカー1"):
    return admin.post("/lockers/items/new", data={"code": code, "name": name})


def lend(admin, code="A-1", number="100001", **extra):
    return admin.post("/lockers/lend", data={"item_code": code, "employee_no": number, **extra})


def items(admin):
    return {i["code"]: i for i in admin.get("/lockers/status.json").get_json()["items"]}


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    add_item(admin, "A-1")
    add_item(admin, "A-2", "ロッカー2")
    return admin


def test_register_and_list(setup):
    r = setup.get("/lockers/")
    assert r.status_code == 200 and "A-2" in r.get_data(as_text=True)
    assert [i["code"] for i in setup.get("/lockers/status.json").get_json()["items"]] == ["A-1", "A-2"]
    assert items(setup)["A-1"]["status"] == "free"


def test_duplicate_code_rejected(setup):
    r = add_item(setup, "A-1")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_register_redirects_and_audits(admin):
    r = add_item(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/lockers/")
    rows = admin.get("/audit.json").get_json()["rows"]
    assert (rows[-1]["module"], rows[-1]["action"], rows[-1]["target"]) == ("lockers", "item_create", "A-1")


def test_edit_name(setup):
    assert setup.post("/lockers/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert items(setup)["A-1"]["name"] == "新名"
    assert setup.post("/lockers/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400


def test_lend_defaults_today_and_due_90_days(setup):
    assert lend(setup).status_code == 302
    i = items(setup)["A-1"]
    assert (i["status"], i["borrower"], i["lent_on"], i["due_on"]) == ("lent", "100001", "2026-06-15", "2026-09-13")


def test_lend_with_date(setup):
    lend(setup, lent_on="2026-06-01")
    assert items(setup)["A-1"]["due_on"] == "2026-08-30"


def test_future_date_rejected_and_today_accepted(setup):
    assert lend(setup, lent_on="2026-06-16").status_code == 400
    assert lend(setup, lent_on="2026-06-15").status_code == 302


def test_bad_date_rejected(setup):
    assert lend(setup, lent_on="abc").status_code == 400


def test_one_item_per_person(setup):
    lend(setup, "A-1")
    r = lend(setup, "A-2")
    assert r.status_code == 400 and items(setup)["A-2"]["status"] == "free"


def test_item_in_use_cannot_be_lent(setup):
    lend(setup, "A-1")
    assert lend(setup, "A-1", "100002").status_code == 400


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", "100002").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400


def test_overdue_boundary_and_status(setup, set_today):
    lend(setup, "A-1", lent_on="2026-06-15")  # 期限 2026-09-13
    set_today("2026-09-13")
    assert items(setup)["A-1"]["status"] == "lent"
    set_today("2026-09-14")
    assert items(setup)["A-1"]["status"] == "overdue"


def test_overdue_borrower_cannot_borrow_new(setup, set_today):
    lend(setup, "A-1")
    set_today("2026-09-14")
    assert lend(setup, "A-2").status_code == 400


def test_return_and_history(setup):
    lend(setup, "A-1")
    assert setup.post("/lockers/return", data={"item_code": "A-1"}).status_code == 302
    assert items(setup)["A-1"]["status"] == "free"
    assert "A-1" in setup.get("/lockers/history").get_data(as_text=True)
    assert lend(setup, "A-2").status_code == 302
    assert setup.post("/lockers/return", data={"item_code": "A-1"}).status_code == 400


def test_delete_rules(setup):
    lend(setup, "A-1")
    assert setup.post("/lockers/items/delete", data={"code": "A-1"}).status_code == 400
    assert setup.post("/lockers/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in items(setup)


def test_filter_q(setup):
    body = setup.get("/lockers/?q=A-2").get_data(as_text=True)
    assert "A-2" in body and "A-1" not in body


def test_employee_cannot_change_but_can_view(app, make_employee):
    make_employee("100001")
    c = app.test_client()
    c.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert c.post("/lockers/items/new", data={"code": "B", "name": "b"}).status_code == 403
    assert c.get("/lockers/status.json").status_code == 200


def test_audit_for_lend_and_return(setup):
    lend(setup)
    setup.post("/lockers/return", data={"item_code": "A-1"})
    actions = [r["action"] for r in setup.get("/audit.json").get_json()["rows"] if r["module"] == "lockers"]
    assert actions[-2:] == ["lend", "return"]

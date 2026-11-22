import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    for code in ("A-1", "A-2", "A-3"):
        assert admin.post("/ladders/items/new", data={"code": code, "name": "脚立" + code}).status_code == 302
    return admin


def items(c):
    return {i["code"]: i for i in c.get("/ladders/status.json").get_json()["items"]}


def lend(c, code="A-1", no="100001", **kw):
    return c.post("/ladders/lend", data={"item_code": code, "employee_no": no, **kw})


def test_create_and_audit(setup):
    assert [(r["action"], r["target"]) for r in setup.get("/audit.json").get_json()["rows"] if r["module"] == "ladders"][0] == ("item_create", "A-1")
    assert list(items(setup)) == ["A-1", "A-2", "A-3"]


def test_duplicate_code_rejected(setup):
    r = setup.post("/ladders/items/new", data={"code": "A-1", "name": "x"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_edit_and_delete(setup):
    assert setup.post("/ladders/items/edit", data={"code": "A-1", "name": "新"}).status_code == 302
    assert items(setup)["A-1"]["name"] == "新"
    assert setup.post("/ladders/items/delete", data={"code": "A-1"}).status_code == 302
    assert "A-1" not in items(setup)
    assert setup.post("/ladders/items/delete", data={"code": "ZZ"}).status_code == 400


def test_lend_defaults_to_today_with_two_day_period(setup):
    assert lend(setup).status_code == 302
    i = items(setup)["A-1"]
    assert (i["status"], i["borrower"], i["lent_on"], i["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-17")


def test_lend_with_date_and_future_rejected(setup):
    assert lend(setup, lent_on="2026-06-14").status_code == 302
    assert items(setup)["A-1"]["due_on"] == "2026-06-16"
    assert lend(setup, "A-2", "100002", lent_on="2026-06-16").status_code == 400
    assert lend(setup, "A-2", "100002", lent_on="2026-06-15").status_code == 302


def test_bad_date_format_rejected(setup):
    assert lend(setup, lent_on="15/06/2026").status_code == 400


def test_one_loan_per_person(setup):
    lend(setup)
    assert lend(setup, "A-2").status_code == 400
    assert items(setup)["A-2"]["status"] == "free"


def test_item_already_lent_cannot_be_lent(setup):
    lend(setup)
    assert lend(setup, "A-1", "100002").status_code == 400


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", "100002").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400


def test_overdue_status_boundary(setup, set_today):
    lend(setup)
    set_today("2026-06-17")
    assert items(setup)["A-1"]["status"] == "lent"
    set_today("2026-06-18")
    assert items(setup)["A-1"]["status"] == "overdue"


def test_overdue_borrower_cannot_borrow_again(setup, set_today):
    lend(setup)
    set_today("2026-06-17")
    r = lend(setup, "A-2")
    assert r.status_code == 400 and "上限" not in r.get_data(as_text=True) and "期限" in r.get_data(as_text=True)
    set_today("2026-06-18")
    r = lend(setup, "A-2")
    assert r.status_code == 400 and "期限を過ぎた" in r.get_data(as_text=True)


def test_return_then_borrow_again_and_history(setup):
    lend(setup)
    assert setup.post("/ladders/return", data={"item_code": "A-1"}).status_code == 302
    assert items(setup)["A-1"]["status"] == "free"
    assert lend(setup, "A-2").status_code == 302
    page = setup.get("/ladders/history").get_data(as_text=True)
    assert "A-1" in page and "100001" in page


def test_return_when_not_lent_rejected(setup):
    assert setup.post("/ladders/return", data={"item_code": "A-1"}).status_code == 400


def test_lent_item_cannot_be_deleted(setup):
    lend(setup)
    assert setup.post("/ladders/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(setup)


def test_staff_only_for_post(setup, make_employee, client):
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/ladders/items/new", data={"code": "B", "name": "b"}).status_code == 403
    assert client.get("/ladders/status.json").status_code == 200


def test_search_and_audit_actions(setup):
    lend(setup)
    setup.post("/ladders/return", data={"item_code": "A-1"})
    page = setup.get("/ladders/?q=A-2").get_data(as_text=True)
    assert "A-2" in page and "A-3" not in page
    actions = [r["action"] for r in setup.get("/audit.json").get_json()["rows"] if r["module"] == "ladders"]
    assert actions[-2:] == ["lend", "return"]


def test_failed_operation_not_audited(setup):
    before = len(setup.get("/audit.json").get_json()["rows"])
    lend(setup, "ZZ")
    assert len(setup.get("/audit.json").get_json()["rows"]) == before

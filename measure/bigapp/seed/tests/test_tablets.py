"""タブレットの貸出のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/tablets/items/new", data={"code": "A-1", "name": "タブレット1"})
    admin.post("/tablets/items/new", data={"code": "A-2", "name": "タブレット2"})
    return admin


def items(client):
    return {i["code"]: i for i in client.get("/tablets/status.json").get_json()["items"]}


def lend(client, code="A-1", no="100001", **extra):
    return client.post("/tablets/lend", data={"item_code": code, "employee_no": no, **extra})


def test_register_item_and_list(setup):
    assert [i["code"] for i in setup.get("/tablets/status.json").get_json()["items"]] == ["A-1", "A-2"]
    assert "タブレット1" in setup.get("/tablets/").get_data(as_text=True)


def test_duplicate_code_rejected(setup):
    r = setup.post("/tablets/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert len(items(setup)) == 2


def test_edit_item_name(setup):
    assert setup.post("/tablets/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert items(setup)["A-1"]["name"] == "新名"
    assert setup.post("/tablets/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400


def test_lend_sets_due_date_7_days(setup):
    r = lend(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/tablets/")
    a = items(setup)["A-1"]
    assert (a["status"], a["borrower"], a["lent_on"], a["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-22")


def test_lend_with_past_date(setup):
    lend(setup, lent_on="2026-06-10")
    assert items(setup)["A-1"]["due_on"] == "2026-06-17"


def test_future_lent_on_rejected_today_accepted(setup):
    assert lend(setup, lent_on="2026-06-16").status_code == 400
    assert items(setup)["A-1"]["status"] == "free"
    assert lend(setup, lent_on="2026-06-15").status_code == 302


def test_invalid_lent_on_rejected(setup):
    assert lend(setup, lent_on="abc").status_code == 400


def test_one_item_per_person(setup):
    lend(setup)
    r = lend(setup, code="A-2")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert items(setup)["A-2"]["status"] == "free"


def test_lent_item_cannot_be_lent(setup):
    lend(setup)
    assert lend(setup, no="100002").status_code == 400


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, no="100002").status_code == 400
    assert lend(setup, no="999999").status_code == 400
    assert items(setup)["A-1"]["status"] == "free"


def test_due_day_is_not_overdue_next_day_is(setup, set_today):
    lend(setup)  # 期限 2026-06-22
    set_today("2026-06-22")
    assert items(setup)["A-1"]["status"] == "lent"
    set_today("2026-06-23")
    assert items(setup)["A-1"]["status"] == "overdue"


def test_person_with_past_due_loan_cannot_borrow(setup, set_today):
    lend(setup)
    set_today("2026-06-23")
    r = lend(setup, code="A-2")
    assert r.status_code == 400 and "期限" in r.get_data(as_text=True)
    assert items(setup)["A-2"]["status"] == "free"


def test_return_then_lend_again_and_history(setup):
    lend(setup)
    assert setup.post("/tablets/return", data={"item_code": "A-1"}).status_code == 302
    assert items(setup)["A-1"]["status"] == "free"
    assert setup.post("/tablets/return", data={"item_code": "A-1"}).status_code == 400
    assert lend(setup, code="A-2").status_code == 302
    page = setup.get("/tablets/history").get_data(as_text=True)
    assert "A-1" in page and "100001" in page


def test_cannot_delete_lent_item(setup):
    lend(setup)
    assert setup.post("/tablets/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(setup)
    assert setup.post("/tablets/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in items(setup)


def test_search_filter(setup):
    page = setup.get("/tablets/?q=A-2").get_data(as_text=True)
    assert "タブレット2" in page and "タブレット1" not in page
    assert "タブレット1" in setup.get("/tablets/?q=ット1").get_data(as_text=True)


def test_employee_cannot_post_but_can_view(setup, client, make_employee):
    make_employee("100003", "一般")
    client.post("/login", data={"employee_no": "100003", "password": "password1"})
    assert client.post("/tablets/items/new", data={"code": "B", "name": "b"}).status_code == 403
    assert lend(client).status_code == 403
    assert client.get("/tablets/status.json").status_code == 200
    assert client.get("/tablets/").status_code == 200


def test_anonymous_redirected(client):
    assert client.post("/tablets/lend", data={}).status_code == 302
    assert client.get("/tablets/status.json").status_code == 302


def test_audit_log_written(setup):
    lend(setup)
    setup.post("/tablets/items/edit", data={"code": "A-1", "name": "n"})
    setup.post("/tablets/return", data={"item_code": "A-1"})
    setup.post("/tablets/items/delete", data={"code": "A-2"})
    rows = [(r["action"], r["target"]) for r in setup.get("/audit.json").get_json()["rows"] if r["module"] == "tablets"]
    assert rows == [
        ("item_create", "A-1"), ("item_create", "A-2"), ("lend", "A-1:100001"),
        ("item_update", "A-1"), ("return", "A-1"), ("item_delete", "A-2"),
    ]


def test_failed_operation_leaves_no_audit(setup):
    before = len(setup.get("/audit.json").get_json()["rows"])
    lend(setup, no="999999")
    assert len(setup.get("/audit.json").get_json()["rows"]) == before

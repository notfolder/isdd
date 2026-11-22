"""ノート PC の貸出のテスト。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "鈴木")
    admin.post("/laptops/items/new", data={"code": "A-1", "name": "ThinkPad"})
    admin.post("/laptops/items/new", data={"code": "A-2", "name": "MacBook"})
    return admin


def status(client):
    return {i["code"]: i for i in client.get("/laptops/status.json").get_json()["items"]}


def lend(client, item="A-1", emp="100001", **kw):
    return client.post("/laptops/lend", data={"item_code": item, "employee_no": emp, **kw})


def test_register_and_list(setup):
    r = setup.get("/laptops/")
    assert r.status_code == 200 and "ThinkPad" in r.get_data(as_text=True)
    assert status(setup)["A-1"]["status"] == "free"


def test_duplicate_code_rejected(setup):
    r = setup.post("/laptops/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_register_redirects(admin):
    r = admin.post("/laptops/items/new", data={"code": "B-1", "name": "x"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/laptops/")


def test_edit_name(setup):
    setup.post("/laptops/items/edit", data={"code": "A-1", "name": "新名"})
    assert status(setup)["A-1"]["name"] == "新名"
    assert setup.post("/laptops/items/edit", data={"code": "ZZ", "name": "x"}).status_code == 400


def test_lend_default_date_and_due_14_days(setup):
    assert lend(setup).status_code == 302
    s = status(setup)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-29")


def test_lend_with_past_date(setup):
    lend(setup, lent_on="2026-06-10")
    assert status(setup)["A-1"]["due_on"] == "2026-06-24"


def test_future_date_rejected_today_ok(setup):
    assert lend(setup, lent_on="2026-06-16").status_code == 400
    assert lend(setup, lent_on="2026-06-15").status_code == 302


def test_bad_date_rejected(setup):
    assert lend(setup, lent_on="あした").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"


def test_lent_item_cannot_be_lent(setup):
    lend(setup)
    assert lend(setup, emp="100002").status_code == 400


def test_one_item_per_person(setup):
    lend(setup)
    r = lend(setup, item="A-2")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, emp="100002").status_code == 400
    assert lend(setup, emp="999999").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"


def test_due_day_is_not_overdue_next_day_is(setup, set_today):
    lend(setup)  # 期限 2026-06-29
    set_today("2026-06-29")
    assert status(setup)["A-1"]["status"] == "lent"
    set_today("2026-06-30")
    assert status(setup)["A-1"]["status"] == "overdue"


def test_no_new_loan_while_holding_past_due_item(setup, set_today):
    lend(setup)
    set_today("2026-06-30")
    r = lend(setup, item="A-2")
    assert r.status_code == 400 and status(setup)["A-2"]["status"] == "free"


def test_return_then_lend_again(setup, set_today):
    lend(setup)
    set_today("2026-06-30")
    assert setup.post("/laptops/return", data={"item_code": "A-1"}).status_code == 302
    assert lend(setup, item="A-2").status_code == 302


def test_return_not_lent_rejected(setup):
    assert setup.post("/laptops/return", data={"item_code": "A-1"}).status_code == 400


def test_history_keeps_returned_loans_newest_first(setup, set_today):
    lend(setup)
    setup.post("/laptops/return", data={"item_code": "A-1"})
    set_today("2026-06-20")
    lend(setup, item="A-2")
    setup.post("/laptops/return", data={"item_code": "A-2"})
    body = setup.get("/laptops/history").get_data(as_text=True)
    assert body.index("A-2") < body.index("A-1")


def test_cannot_delete_lent_item(setup):
    lend(setup)
    assert setup.post("/laptops/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(setup)


def test_delete_free_item(setup):
    assert setup.post("/laptops/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(setup)


def test_filter_q(setup):
    body = setup.get("/laptops/?q=Mac").get_data(as_text=True)
    assert "MacBook" in body and "ThinkPad" not in body
    assert "A-1" in setup.get("/laptops/?q=A-1").get_data(as_text=True)


def test_status_json_sorted_by_code(setup):
    assert [i["code"] for i in setup.get("/laptops/status.json").get_json()["items"]] == ["A-1", "A-2"]


def test_non_staff_cannot_post(app, setup, make_employee):
    c = app.test_client()
    c.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert c.post("/laptops/items/new", data={"code": "C", "name": "x"}).status_code == 403
    assert c.get("/laptops/status.json").status_code == 200


def test_audit_log_written(app, setup):
    lend(setup)
    setup.post("/laptops/return", data={"item_code": "A-1"})
    setup.post("/laptops/items/edit", data={"code": "A-1", "name": "n"})
    setup.post("/laptops/items/delete", data={"code": "A-1"})
    with app.app_context():
        actions = [r["action"] for r in get_db().execute("SELECT action FROM audit_log WHERE module = 'laptops' ORDER BY id")]
    assert actions == ["item_create", "item_create", "lend", "return", "item_update", "item_delete"]


def test_rejected_writes_nothing_to_audit(app, setup):
    lend(setup, item="NOPE")
    with app.app_context():
        n = get_db().execute("SELECT COUNT(*) FROM audit_log WHERE action = 'lend'").fetchone()[0]
    assert n == 0

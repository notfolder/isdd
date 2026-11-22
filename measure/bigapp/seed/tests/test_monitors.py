"""モニターの貸出のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    """物 A-1, A-2, A-3 と社員 100001, 100002 を用意する。"""
    for code in ("A-1", "A-2", "A-3"):
        assert admin.post("/monitors/items/new", data={"code": code, "name": f"モニター {code}"}).status_code == 302
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    return admin


def lend(c, item, no="100001", lent_on=None):
    data = {"item_code": item, "employee_no": no}
    if lent_on:
        data["lent_on"] = lent_on
    return c.post("/monitors/lend", data=data)


def items(c):
    return {i["code"]: i for i in c.get("/monitors/status.json").get_json()["items"]}


def audit_rows(c):
    return [(r["module"], r["action"], r["target"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "monitors"]


def test_register_and_list(setup):
    page = setup.get("/monitors/").get_data(as_text=True)
    assert "A-1" in page and "モニター A-2" in page
    assert items(setup)["A-1"]["status"] == "free"
    assert [i["code"] for i in setup.get("/monitors/status.json").get_json()["items"]] == ["A-1", "A-2", "A-3"]


def test_search_filters_by_code_or_name(setup):
    assert "A-2" not in setup.get("/monitors/?q=A-1").get_data(as_text=True)
    assert "A-3" in setup.get("/monitors/?q=モニター A-3").get_data(as_text=True)


def test_duplicate_code_rejected(setup):
    r = setup.post("/monitors/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_empty_code_or_name_rejected(setup):
    assert setup.post("/monitors/items/new", data={"code": "", "name": "x"}).status_code == 400
    assert setup.post("/monitors/items/new", data={"code": "B-1", "name": ""}).status_code == 400


def test_edit_item_name(setup):
    assert setup.post("/monitors/items/edit", data={"code": "A-1", "name": "新しい名前"}).status_code == 302
    assert items(setup)["A-1"]["name"] == "新しい名前"
    assert setup.post("/monitors/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400


def test_delete_item_and_lent_item_cannot_be_deleted(setup):
    assert setup.post("/monitors/items/delete", data={"code": "A-3"}).status_code == 302
    assert "A-3" not in items(setup)
    lend(setup, "A-1")
    assert setup.post("/monitors/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(setup)


def test_lend_sets_due_30_days_after(setup):
    assert lend(setup, "A-1").status_code == 302
    a = items(setup)["A-1"]
    assert (a["status"], a["borrower"], a["lent_on"], a["due_on"]) == ("lent", "100001", "2026-06-15", "2026-07-15")


def test_lend_with_explicit_date(setup):
    lend(setup, "A-1", lent_on="2026-06-01")
    assert items(setup)["A-1"]["due_on"] == "2026-07-01"


def test_future_lent_on_rejected_but_today_ok(setup):
    assert lend(setup, "A-1", lent_on="2026-06-16").status_code == 400
    assert items(setup)["A-1"]["status"] == "free"
    assert lend(setup, "A-1", lent_on="2026-06-15").status_code == 302


def test_bad_date_format_rejected(setup):
    assert lend(setup, "A-1", lent_on="2026/06/01").status_code == 400


def test_lent_item_cannot_be_lent_again(setup):
    lend(setup, "A-1")
    r = lend(setup, "A-1", "100002")
    assert r.status_code == 400
    assert items(setup)["A-1"]["borrower"] == "100001"


def test_limit_two_per_person(setup):
    assert lend(setup, "A-1").status_code == 302
    assert lend(setup, "A-2").status_code == 302
    assert lend(setup, "A-3").status_code == 400
    assert lend(setup, "A-3", "100002").status_code == 302


def test_return_frees_slot_and_keeps_history(setup):
    lend(setup, "A-1")
    lend(setup, "A-2")
    assert setup.post("/monitors/return", data={"item_code": "A-1"}).status_code == 302
    assert items(setup)["A-1"]["status"] == "free"
    assert lend(setup, "A-3").status_code == 302
    history = setup.get("/monitors/history").get_data(as_text=True)
    assert "A-1" in history and "100001" in history


def test_history_is_newest_first(setup):
    lend(setup, "A-1")
    setup.post("/monitors/return", data={"item_code": "A-1"})
    lend(setup, "A-2")
    setup.post("/monitors/return", data={"item_code": "A-2"})
    history = setup.get("/monitors/history").get_data(as_text=True)
    assert history.index("A-2") < history.index("A-1")


def test_return_of_free_item_rejected(setup):
    assert setup.post("/monitors/return", data={"item_code": "A-1"}).status_code == 400


def test_overdue_boundary(setup, set_today):
    lend(setup, "A-1", lent_on="2026-06-15")  # 期限 2026-07-15
    set_today("2026-07-15")
    assert items(setup)["A-1"]["status"] == "lent"  # 期限当日は延滞でない
    set_today("2026-07-16")
    assert items(setup)["A-1"]["status"] == "overdue"


def test_late_borrower_cannot_borrow_but_on_due_day_can(setup, set_today):
    lend(setup, "A-1", lent_on="2026-06-15")
    set_today("2026-07-15")
    assert lend(setup, "A-2").status_code == 302
    setup.post("/monitors/return", data={"item_code": "A-2"})
    set_today("2026-07-16")
    assert lend(setup, "A-2").status_code == 400
    assert lend(setup, "A-2", "100002").status_code == 302


def test_late_borrower_can_borrow_after_return(setup, set_today):
    lend(setup, "A-1", lent_on="2026-05-01")
    assert lend(setup, "A-2").status_code == 400
    setup.post("/monitors/return", data={"item_code": "A-1"})
    assert lend(setup, "A-2").status_code == 302


def test_retired_and_unknown_employee_rejected(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", "100002").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400
    assert lend(setup, "Z-9", "100001").status_code == 400


def test_employee_cannot_change_data(setup, client, make_employee):
    make_employee("100003", "一般")
    from app.core.db import ADMIN_NO  # noqa: F401

    c = setup.application.test_client()
    # パスワードは既定値
    c.post("/login", data={"employee_no": "100003", "password": "password1"})
    assert c.post("/monitors/items/new", data={"code": "X", "name": "x"}).status_code == 403
    assert lend(c, "A-1").status_code == 403
    assert c.get("/monitors/status.json").status_code == 200
    assert "X" not in items(c)


def test_not_logged_in_redirects(client):
    assert client.get("/monitors/status.json").status_code == 302
    assert client.post("/monitors/items/new", data={"code": "X", "name": "x"}).status_code == 302


def test_rejected_request_does_not_write_audit(setup):
    before = audit_rows(setup)
    lend(setup, "Z-9")
    assert audit_rows(setup) == before


def test_audit_records_each_operation(setup):
    lend(setup, "A-1")
    setup.post("/monitors/return", data={"item_code": "A-1"})
    setup.post("/monitors/items/edit", data={"code": "A-1", "name": "改"})
    setup.post("/monitors/items/delete", data={"code": "A-3"})
    actions = [a for _, a, _ in audit_rows(setup)]
    assert actions == ["item_create"] * 3 + ["lend", "return", "item_update", "item_delete"]

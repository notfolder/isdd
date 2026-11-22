"""ヘルメットの貸出のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    for code in ("A-1", "A-2", "A-3"):
        admin.post("/helmets/items/new", data={"code": code, "name": "ヘルメット " + code})
    return admin


def lend(c, item, emp="100001", on=None):
    data = {"item_code": item, "employee_no": emp}
    if on:
        data["lent_on"] = on
    return c.post("/helmets/lend", data=data)


def status(c):
    return {i["code"]: i for i in c.get("/helmets/status.json").get_json()["items"]}


def audit_actions(c):
    return [r["action"] for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "helmets"]


def test_item_create_and_list(setup):
    r = setup.get("/helmets/")
    assert r.status_code == 200 and "A-1" in r.get_data(as_text=True)
    assert audit_actions(setup).count("item_create") == 3


def test_duplicate_code_rejected(setup):
    r = setup.post("/helmets/items/new", data={"code": "A-1", "name": "x"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert len(status(setup)) == 3


def test_item_edit(setup):
    r = setup.post("/helmets/items/edit", data={"code": "A-1", "name": "新名称"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/helmets/")
    assert status(setup)["A-1"]["name"] == "新名称"
    assert setup.post("/helmets/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400


def test_search_filter(setup):
    html = setup.get("/helmets/?q=A-2").get_data(as_text=True)
    assert "A-2" in html and "A-3" not in html


def test_lend_default_date_and_due(setup):
    r = lend(setup, "A-1")
    assert r.status_code == 302
    s = status(setup)["A-1"]
    assert s["status"] == "lent" and s["borrower"] == "100001"
    assert s["lent_on"] == "2026-06-15" and s["due_on"] == "2026-06-25"
    assert "lend" in audit_actions(setup)


def test_lend_with_date(setup):
    lend(setup, "A-1", on="2026-06-01")
    assert status(setup)["A-1"]["due_on"] == "2026-06-11"


def test_future_date_rejected_today_ok(setup):
    assert lend(setup, "A-1", on="2026-06-16").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"
    assert lend(setup, "A-1", on="2026-06-15").status_code == 302


def test_bad_date_rejected(setup):
    assert lend(setup, "A-1", on="2026/06/01").status_code == 400


def test_limit_two_at_once(setup):
    assert lend(setup, "A-1").status_code == 302
    assert lend(setup, "A-2").status_code == 302
    r = lend(setup, "A-3")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert lend(setup, "A-3", emp="100002").status_code == 302


def test_cannot_lend_lent_item(setup):
    lend(setup, "A-1")
    assert lend(setup, "A-1", emp="100002").status_code == 400
    assert status(setup)["A-1"]["borrower"] == "100001"


def test_due_day_not_expired_next_day_expired(setup, set_today):
    lend(setup, "A-1", on="2026-06-05")  # 期限 06-15 = 今日
    assert status(setup)["A-1"]["status"] == "lent"
    assert lend(setup, "A-2").status_code == 302
    set_today("2026-06-16")
    assert status(setup)["A-1"]["status"] == "overdue"


def test_expired_holder_cannot_borrow(setup, set_today):
    lend(setup, "A-1")
    set_today("2026-06-26")
    assert lend(setup, "A-2").status_code == 400
    assert lend(setup, "A-2", emp="100002").status_code == 302


def test_expired_boundary_not_blocked(setup, set_today):
    lend(setup, "A-1")
    set_today("2026-06-25")
    assert lend(setup, "A-2").status_code == 302


def test_return_and_history(setup):
    lend(setup, "A-1")
    r = setup.post("/helmets/return", data={"item_code": "A-1"})
    assert r.status_code == 302
    assert status(setup)["A-1"]["status"] == "free"
    assert "A-1" in setup.get("/helmets/history").get_data(as_text=True)
    assert "return" in audit_actions(setup)
    assert setup.post("/helmets/return", data={"item_code": "A-1"}).status_code == 400
    assert lend(setup, "A-1", emp="100002").status_code == 302


def test_delete_rules(setup):
    lend(setup, "A-1")
    assert setup.post("/helmets/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(setup)
    assert setup.post("/helmets/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(setup)
    assert "item_delete" in audit_actions(setup)


def test_retired_and_unknown_employee(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", emp="100002").status_code == 400
    assert lend(setup, "A-1", emp="999999").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"


def test_rejected_leaves_no_audit(setup):
    before = len(audit_actions(setup))
    lend(setup, "A-1", emp="999999")
    assert len(audit_actions(setup)) == before


def test_staff_only_for_post(client, setup, make_employee):
    make_employee("100003", "一般")
    client.post("/logout")
    client.post("/login", data={"employee_no": "100003", "password": "password1"})
    assert lend(client, "A-1").status_code == 403
    assert client.post("/helmets/items/new", data={"code": "B", "name": "b"}).status_code == 403
    assert client.get("/helmets/status.json").status_code == 200
    assert status(client)["A-1"]["status"] == "free"


def test_status_json_sorted(setup):
    assert list(status(setup)) == ["A-1", "A-2", "A-3"]

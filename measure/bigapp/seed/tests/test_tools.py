"""工具の貸出のテスト。"""

import pytest


@pytest.fixture
def setup(admin, make_employee):
    """物 A-1〜A-3 と社員 100001 を用意する。"""
    make_employee("100001", "山田")
    for code in ("A-1", "A-2", "A-3"):
        admin.post("/tools/items/new", data={"code": code, "name": f"工具{code}"})
    return admin


def lend(c, code, no="100001", on=None):
    data = {"item_code": code, "employee_no": no}
    if on:
        data["lent_on"] = on
    return c.post("/tools/lend", data=data)


def items(c):
    return {i["code"]: i for i in c.get("/tools/status.json").get_json()["items"]}


def actions(c):
    return [(r["module"], r["action"], r["target"]) for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "tools"]


def test_register_item_and_duplicate(setup):
    assert setup.post("/tools/items/new", data={"code": "B-1", "name": "ドリル"}).status_code == 302
    r = setup.post("/tools/items/new", data={"code": "B-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert setup.post("/tools/items/new", data={"code": "", "name": "x"}).status_code == 400


def test_edit_and_delete_item(setup):
    assert setup.post("/tools/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert items(setup)["A-1"]["name"] == "新名"
    assert setup.post("/tools/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400
    assert setup.post("/tools/items/delete", data={"code": "A-1"}).status_code == 302
    assert "A-1" not in items(setup)


def test_cannot_delete_lent_item(setup):
    lend(setup, "A-1")
    assert setup.post("/tools/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(setup)


def test_lend_default_today_and_due_in_7_days(setup):
    assert lend(setup, "A-1").status_code == 302
    i = items(setup)["A-1"]
    assert (i["status"], i["borrower"], i["lent_on"], i["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-22")


def test_lend_with_past_date_and_future_rejected(setup):
    assert lend(setup, "A-1", on="2026-06-10").status_code == 302
    assert items(setup)["A-1"]["due_on"] == "2026-06-17"
    assert lend(setup, "A-2", on="2026-06-16").status_code == 400
    assert lend(setup, "A-2", on="2026-06-15").status_code == 302
    assert lend(setup, "A-3", on="bad").status_code == 400


def test_cannot_lend_lent_item(setup, make_employee):
    make_employee("100002", "佐藤")
    lend(setup, "A-1")
    assert lend(setup, "A-1", "100002").status_code == 400


def test_limit_two_per_person(setup):
    assert lend(setup, "A-1").status_code == 302
    assert lend(setup, "A-2").status_code == 302
    assert lend(setup, "A-3").status_code == 400
    setup.post("/tools/return", data={"item_code": "A-1"})
    assert lend(setup, "A-3").status_code == 302


def test_expired_boundary(setup, set_today):
    lend(setup, "A-1", on="2026-06-08")  # 期限 2026-06-15 = 今日。まだ期限切れではない
    assert items(setup)["A-1"]["status"] == "lent"
    assert lend(setup, "A-2").status_code == 302
    set_today("2026-06-16")
    assert items(setup)["A-1"]["status"] == "overdue"


def test_no_new_loan_while_holding_expired(setup, set_today):
    lend(setup, "A-1")
    set_today("2026-06-23")  # 期限 06-22 の翌日
    r = lend(setup, "A-2")
    assert r.status_code == 400 and "期限" in r.get_data(as_text=True)
    set_today("2026-06-22")
    assert lend(setup, "A-2").status_code == 302


def test_retired_and_unknown_employee_rejected(setup, make_employee):
    make_employee("100003", "退職者")
    setup.post("/employees/retire", data={"employee_no": "100003"})
    assert lend(setup, "A-1", "100003").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400
    assert lend(setup, "Z-9").status_code == 400
    assert items(setup)["A-1"]["status"] == "free"


def test_return_keeps_history_and_frees_item(setup):
    lend(setup, "A-1", on="2026-06-10")
    assert setup.post("/tools/return", data={"item_code": "A-1"}).status_code == 302
    assert items(setup)["A-1"]["status"] == "free"
    assert setup.post("/tools/return", data={"item_code": "A-1"}).status_code == 400
    page = setup.get("/tools/history").get_data(as_text=True)
    assert "A-1" in page and "2026-06-10" in page and "2026-06-17" in page


def test_history_newest_first(setup):
    lend(setup, "A-1")
    setup.post("/tools/return", data={"item_code": "A-1"})
    lend(setup, "A-2")
    setup.post("/tools/return", data={"item_code": "A-2"})
    page = setup.get("/tools/history").get_data(as_text=True)
    assert page.index("A-2") < page.index("A-1")


def test_status_json_sorted_and_null_fields(setup):
    lend(setup, "A-2")
    data = setup.get("/tools/status.json").get_json()["items"]
    assert [i["code"] for i in data] == ["A-1", "A-2", "A-3"]
    assert data[0] == {"code": "A-1", "name": "工具A-1", "status": "free", "borrower": None, "lent_on": None, "due_on": None}


def test_search_filter(setup):
    page = setup.get("/tools/?q=A-2").get_data(as_text=True)
    assert "A-2" in page and "A-3" not in page


def test_permissions(setup, app):
    client = app.test_client()
    assert client.get("/tools/status.json").status_code == 302  # 未ログイン
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.get("/tools/status.json").status_code == 200
    assert client.get("/tools/").status_code == 200
    assert client.post("/tools/items/new", data={"code": "C-1", "name": "x"}).status_code == 403
    assert lend(client, "A-1").status_code == 403
    assert "C-1" not in items(client)


def test_audit_records(setup):
    lend(setup, "A-1")
    setup.post("/tools/return", data={"item_code": "A-1"})
    setup.post("/tools/items/edit", data={"code": "A-1", "name": "n"})
    setup.post("/tools/items/delete", data={"code": "A-3"})
    lend(setup, "A-1", on="2999-01-01")  # 拒否された操作は残らない
    names = [a for _, a, _ in actions(setup)]
    assert names == ["item_create"] * 3 + ["lend", "return", "item_update", "item_delete"]

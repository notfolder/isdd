"""安全ベストの貸出のテスト。"""

import pytest


@pytest.fixture
def vests(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    for code in ("A-1", "A-2", "A-3", "B-1"):
        assert admin.post("/safety_vests/items/new", data={"code": code, "name": f"ベスト{code}"}).status_code == 302
    return admin


def lend(c, code, no="100001", on=None):
    data = {"item_code": code, "employee_no": no}
    if on:
        data["lent_on"] = on
    return c.post("/safety_vests/lend", data=data)


def items(c):
    return {i["code"]: i for i in c.get("/safety_vests/status.json").get_json()["items"]}


def test_register_and_duplicate(vests):
    r = vests.post("/safety_vests/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert list(items(vests)) == ["A-1", "A-2", "A-3", "B-1"]


def test_edit_and_delete_item(vests):
    assert vests.post("/safety_vests/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert items(vests)["A-1"]["name"] == "新名"
    assert vests.post("/safety_vests/items/delete", data={"code": "A-1"}).status_code == 302
    assert "A-1" not in items(vests)
    assert vests.post("/safety_vests/items/delete", data={"code": "A-1"}).status_code == 400


def test_lend_sets_due_14_days(vests):
    r = lend(vests, "A-1")
    assert r.status_code == 302 and r.headers["Location"].endswith("/safety_vests/")
    a = items(vests)["A-1"]
    assert (a["status"], a["borrower"], a["lent_on"], a["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-29")


def test_lend_with_date_and_future_rejected(vests):
    assert lend(vests, "A-1", on="2026-06-10").status_code == 302
    assert items(vests)["A-1"]["due_on"] == "2026-06-24"
    assert lend(vests, "A-2", on="2026-06-15").status_code == 302  # 今日は可
    assert lend(vests, "A-3", no="100002", on="2026-06-16").status_code == 400  # 明日は不可
    assert lend(vests, "A-3", no="100002", on="abc").status_code == 400


def test_limit_two_loans(vests):
    assert lend(vests, "A-1").status_code == 302
    assert lend(vests, "A-2").status_code == 302
    r = lend(vests, "A-3")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert items(vests)["A-3"]["status"] == "free"
    assert lend(vests, "A-3", no="100002").status_code == 302


def test_lent_item_cannot_be_lent_again(vests):
    lend(vests, "A-1")
    assert lend(vests, "A-1", no="100002").status_code == 400


def test_overdue_boundary(vests, set_today):
    lend(vests, "A-1")  # 期限 06-29
    set_today("2026-06-29")  # 期限の当日は延滞ではない
    assert items(vests)["A-1"]["status"] == "lent"
    assert lend(vests, "A-2").status_code == 302
    set_today("2026-06-30")
    assert items(vests)["A-1"]["status"] == "overdue"


def test_overdue_borrower_cannot_borrow(vests, set_today):
    lend(vests, "A-1")
    set_today("2026-06-30")
    assert lend(vests, "A-2").status_code == 400
    assert lend(vests, "A-2", no="100002").status_code == 302  # 他の社員は借りられる
    vests.post("/safety_vests/return", data={"item_code": "A-1"})
    assert lend(vests, "A-3").status_code == 302  # 返却すれば再び借りられる


def test_return_and_history(vests, set_today):
    lend(vests, "A-1")
    set_today("2026-06-20")
    assert vests.post("/safety_vests/return", data={"item_code": "A-1"}).status_code == 302
    assert items(vests)["A-1"]["status"] == "free"
    assert items(vests)["A-1"]["borrower"] is None
    body = vests.get("/safety_vests/history").get_data(as_text=True)
    assert "A-1" in body and "2026-06-20" in body
    assert vests.post("/safety_vests/return", data={"item_code": "A-1"}).status_code == 400


def test_lent_item_cannot_be_deleted(vests):
    lend(vests, "A-1")
    assert vests.post("/safety_vests/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(vests)


def test_retired_and_unknown_employee_rejected(vests):
    vests.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(vests, "A-1", no="100002").status_code == 400
    assert lend(vests, "A-1", no="999999").status_code == 400
    assert items(vests)["A-1"]["status"] == "free"


def test_only_staff_can_change(app, vests, make_employee):
    other = app.test_client()
    other.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert other.post("/safety_vests/items/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert lend(other, "A-1").status_code == 403
    assert other.get("/safety_vests/").status_code == 200
    assert other.get("/safety_vests/status.json").status_code == 200
    anon = app.test_client()
    assert anon.post("/safety_vests/return", data={"item_code": "A-1"}).status_code == 302


def test_audit_records_each_operation(vests):
    lend(vests, "A-1")
    vests.post("/safety_vests/return", data={"item_code": "A-1"})
    vests.post("/safety_vests/items/edit", data={"code": "A-2", "name": "x"})
    vests.post("/safety_vests/items/delete", data={"code": "A-2"})
    lend(vests, "A-1", no="999999")  # 失敗は残さない
    rows = [(r["action"], r["target"]) for r in vests.get("/audit.json").get_json()["rows"] if r["module"] == "safety_vests"]
    assert rows[-4:] == [("lend", "A-1"), ("return", "A-1"), ("item_update", "A-2"), ("item_delete", "A-2")]
    assert rows.count(("item_create", "A-1")) == 1 and len(rows) == 8


def test_search_filter(vests):
    body = vests.get("/safety_vests/?q=B-1").get_data(as_text=True)
    assert "B-1" in body and "A-2" not in body

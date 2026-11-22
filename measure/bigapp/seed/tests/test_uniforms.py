"""制服の貸与のテスト。今日は conftest で 2026-06-15。"""

import pytest


@pytest.fixture
def items(admin):
    for code in ("A-1", "A-2", "A-3"):
        admin.post("/uniforms/items/new", data={"code": code, "name": f"制服 {code}"})
    return admin


def status(client):
    return {i["code"]: i for i in client.get("/uniforms/status.json").get_json()["items"]}


def lend(client, code, no, lent_on=None):
    data = {"item_code": code, "employee_no": no}
    if lent_on:
        data["lent_on"] = lent_on
    return client.post("/uniforms/lend", data=data)


def audit_rows(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"]]


def test_register_item_and_list(items):
    body = items.get("/uniforms/").get_data(as_text=True)
    assert "A-1" in body and "制服 A-2" in body
    assert [i["code"] for i in items.get("/uniforms/status.json").get_json()["items"]] == ["A-1", "A-2", "A-3"]


def test_duplicate_code_rejected(items):
    r = items.post("/uniforms/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert len(status(items)) == 3


def test_edit_and_delete_item(items):
    assert items.post("/uniforms/items/edit", data={"code": "A-1", "name": "新名称"}).status_code == 302
    assert status(items)["A-1"]["name"] == "新名称"
    assert items.post("/uniforms/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400
    assert items.post("/uniforms/items/delete", data={"code": "A-1"}).status_code == 302
    assert "A-1" not in status(items)


def test_search_by_code_or_name(items):
    body = items.get("/uniforms/?q=A-2").get_data(as_text=True)
    assert "A-2" in body and "A-3" not in body


def test_lend_sets_due_after_60_days(items, make_employee):
    make_employee("100001")
    r = lend(items, "A-1", "100001")
    assert r.status_code == 302 and r.headers["Location"].endswith("/uniforms/")
    s = status(items)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-08-14")


def test_lent_on_default_and_future_rejected(items, make_employee):
    make_employee("100001")
    assert lend(items, "A-1", "100001", "2026-06-16").status_code == 400
    assert lend(items, "A-1", "100001", "2026-06-15").status_code == 302
    assert lend(items, "A-2", "100001", "2026-13-40").status_code == 400


def test_unknown_or_retired_employee_rejected(items, make_employee):
    make_employee("100001")
    items.post("/employees/retire", data={"employee_no": "100001"})
    assert lend(items, "A-1", "100001").status_code == 400
    assert lend(items, "A-1", "999999").status_code == 400
    assert status(items)["A-1"]["status"] == "free"


def test_lent_item_cannot_be_lent_or_deleted(items, make_employee):
    make_employee("100001")
    make_employee("100002")
    lend(items, "A-1", "100001")
    assert lend(items, "A-1", "100002").status_code == 400
    assert items.post("/uniforms/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(items)


def test_limit_two_at_a_time(items, make_employee):
    make_employee("100001")
    assert lend(items, "A-1", "100001").status_code == 302
    assert lend(items, "A-2", "100001").status_code == 302
    assert lend(items, "A-3", "100001").status_code == 400
    items.post("/uniforms/return", data={"item_code": "A-1"})
    assert lend(items, "A-3", "100001").status_code == 302


def test_due_day_is_not_overdue_next_day_is(items, make_employee, set_today):
    make_employee("100001")
    lend(items, "A-1", "100001")  # 期限 2026-08-14
    set_today("2026-08-14")
    assert status(items)["A-1"]["status"] == "lent"
    assert lend(items, "A-2", "100001").status_code == 302
    set_today("2026-08-15")
    assert status(items)["A-1"]["status"] == "overdue"
    assert lend(items, "A-3", "100001").status_code == 400


def test_overdue_blocks_only_that_employee(items, make_employee, set_today):
    make_employee("100001")
    make_employee("100002")
    lend(items, "A-1", "100001")
    set_today("2026-09-01")
    assert lend(items, "A-2", "100001").status_code == 400
    assert lend(items, "A-2", "100002", "2026-09-01").status_code == 302


def test_return_keeps_history_and_frees_item(items, make_employee, set_today):
    make_employee("100001")
    lend(items, "A-1", "100001")
    set_today("2026-06-20")
    assert items.post("/uniforms/return", data={"item_code": "A-1"}).status_code == 302
    assert status(items)["A-1"]["status"] == "free"
    body = items.get("/uniforms/history").get_data(as_text=True)
    assert "A-1" in body and "2026-06-20" in body
    assert items.post("/uniforms/return", data={"item_code": "A-1"}).status_code == 400


def test_returning_clears_overdue_block(items, make_employee, set_today):
    make_employee("100001")
    lend(items, "A-1", "100001")
    set_today("2026-09-01")
    items.post("/uniforms/return", data={"item_code": "A-1"})
    assert lend(items, "A-2", "100001").status_code == 302


def test_non_staff_cannot_post(items, make_employee, client):
    make_employee("100001")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/uniforms/items/new", data={"code": "B-1", "name": "x"}).status_code == 403
    assert lend(client, "A-1", "100001").status_code == 403
    assert client.get("/uniforms/status.json").status_code == 200


def test_audit_records(items, make_employee):
    make_employee("100001")
    lend(items, "A-1", "100001")
    items.post("/uniforms/return", data={"item_code": "A-1"})
    items.post("/uniforms/items/edit", data={"code": "A-1", "name": "改"})
    items.post("/uniforms/items/delete", data={"code": "A-1"})
    rows = [r for r in audit_rows(items) if r[0] == "uniforms"]
    assert rows[-4:] == [("uniforms", "lend", "A-1"), ("uniforms", "return", "A-1"), ("uniforms", "item_update", "A-1"), ("uniforms", "item_delete", "A-1")]
    assert ("uniforms", "item_create", "A-1") in rows


def test_failed_operation_not_audited(items):
    before = len(audit_rows(items))
    items.post("/uniforms/items/new", data={"code": "A-1", "name": "重複"})
    assert len(audit_rows(items)) == before

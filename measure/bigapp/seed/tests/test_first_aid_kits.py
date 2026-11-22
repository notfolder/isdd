"""救急箱の貸出のテスト。きまりを 1 つずつ確かめる。今日は 2026-06-15（conftest）。"""

import pytest


def add_item(admin, code="A-1", name="救急箱 1"):
    return admin.post("/first_aid_kits/items/new", data={"code": code, "name": name})


def lend(admin, code="A-1", employee_no="100001", lent_on=None):
    data = {"item_code": code, "employee_no": employee_no}
    if lent_on is not None:
        data["lent_on"] = lent_on
    return admin.post("/first_aid_kits/lend", data=data)


def items(admin):
    return {i["code"]: i for i in admin.get("/first_aid_kits/status.json").get_json()["items"]}


def audit_rows(admin):
    return [(r["module"], r["action"], r["target"]) for r in admin.get("/audit.json").get_json()["rows"] if r["module"] == "first_aid_kits"]


@pytest.fixture
def ready(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    add_item(admin, "A-1")
    add_item(admin, "A-2", "救急箱 2")
    return admin


def test_register_item_redirects_and_logs(admin):
    r = add_item(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/first_aid_kits/")
    assert items(admin)["A-1"]["status"] == "free"
    assert ("first_aid_kits", "item_create", "A-1") in audit_rows(admin)


def test_duplicate_code_is_rejected(admin):
    add_item(admin)
    r = add_item(admin, "A-1", "別")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert len(items(admin)) == 1


def test_edit_item_name(admin):
    add_item(admin)
    assert admin.post("/first_aid_kits/items/edit", data={"code": "A-1", "name": "新しい名前"}).status_code == 302
    assert items(admin)["A-1"]["name"] == "新しい名前"
    assert admin.post("/first_aid_kits/items/edit", data={"code": "Z", "name": "x"}).status_code == 400


def test_lend_default_date_and_due_is_seven_days(ready):
    assert lend(ready).status_code == 302
    i = items(ready)["A-1"]
    assert (i["status"], i["borrower"], i["lent_on"], i["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-22")
    assert ("first_aid_kits", "lend", "A-1") in audit_rows(ready)


def test_lend_with_past_date_sets_due(ready):
    lend(ready, lent_on="2026-06-10")
    assert items(ready)["A-1"]["due_on"] == "2026-06-17"


def test_future_lent_on_rejected_and_today_accepted(ready):
    assert lend(ready, lent_on="2026-06-16").status_code == 400
    assert items(ready)["A-1"]["status"] == "free"
    assert lend(ready, lent_on="2026-06-15").status_code == 302


def test_bad_lent_on_format_rejected(ready):
    assert lend(ready, lent_on="2026/06/10").status_code == 400
    assert lend(ready, lent_on="abc").status_code == 400


def test_item_already_lent_cannot_be_lent(ready):
    lend(ready)
    r = lend(ready, employee_no="100002")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert items(ready)["A-1"]["borrower"] == "100001"


def test_one_person_one_item_at_a_time(ready):
    lend(ready, "A-1")
    assert lend(ready, "A-2").status_code == 400
    assert items(ready)["A-2"]["status"] == "free"


def test_retired_or_unknown_employee_rejected(ready):
    ready.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(ready, employee_no="100002").status_code == 400
    assert lend(ready, employee_no="999999").status_code == 400
    assert lend(ready, code="NOPE").status_code == 400


def test_due_day_is_not_expired_but_next_day_is(ready, set_today):
    lend(ready)  # 期限 2026-06-22
    set_today("2026-06-22")
    assert items(ready)["A-1"]["status"] == "lent"
    set_today("2026-06-23")
    assert items(ready)["A-1"]["status"] == "overdue"


def test_expired_loan_blocks_new_lend_with_expired_reason(ready, set_today):
    lend(ready)
    set_today("2026-06-23")
    r = lend(ready, "A-2")
    assert r.status_code == 400 and "期限を過ぎた" in r.get_data(as_text=True)


def test_return_records_history_and_frees_item(ready):
    lend(ready)
    r = ready.post("/first_aid_kits/return", data={"item_code": "A-1"})
    assert r.status_code == 302
    assert items(ready)["A-1"]["status"] == "free"
    page = ready.get("/first_aid_kits/history").get_data(as_text=True)
    assert "A-1" in page and "100001" in page and "2026-06-22" in page
    assert ("first_aid_kits", "return", "A-1") in audit_rows(ready)
    assert lend(ready, "A-2").status_code == 302  # 返却後はまた借りられる


def test_return_when_not_lent_rejected(ready):
    assert ready.post("/first_aid_kits/return", data={"item_code": "A-1"}).status_code == 400


def test_cannot_delete_lent_item_but_can_delete_free(ready):
    lend(ready)
    assert ready.post("/first_aid_kits/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in items(ready)
    assert ready.post("/first_aid_kits/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in items(ready)
    assert ("first_aid_kits", "item_delete", "A-2") in audit_rows(ready)


def test_rejected_operation_leaves_no_audit_row(ready):
    before = len(audit_rows(ready))
    lend(ready, employee_no="999999")
    assert len(audit_rows(ready)) == before


def test_search_filters_by_code_or_name(ready):
    html = ready.get("/first_aid_kits/?q=A-2").get_data(as_text=True)
    assert 'data-code="A-2"' in html and 'data-code="A-1"' not in html
    html = ready.get("/first_aid_kits/?q=救急箱 1").get_data(as_text=True)
    assert 'data-code="A-1"' in html and 'data-code="A-2"' not in html


def test_status_json_sorted_by_code_with_null_fields(ready):
    ready.post("/first_aid_kits/items/new", data={"code": "A-0", "name": "x"})
    rows = ready.get("/first_aid_kits/status.json").get_json()["items"]
    assert [r["code"] for r in rows] == ["A-0", "A-1", "A-2"]
    assert rows[0] == {"code": "A-0", "name": "x", "status": "free", "borrower": None, "lent_on": None, "due_on": None}


def test_non_staff_cannot_post_but_can_view(ready, client, make_employee):
    ready.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/first_aid_kits/items/new", data={"code": "B", "name": "b"}).status_code == 403
    assert client.post("/first_aid_kits/lend", data={"item_code": "A-1", "employee_no": "100001"}).status_code == 403
    assert client.get("/first_aid_kits/status.json").status_code == 200
    assert client.get("/first_aid_kits/").status_code == 200

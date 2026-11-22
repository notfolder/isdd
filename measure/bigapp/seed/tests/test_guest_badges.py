"""来客用入館証の貸出のテスト。"""

import pytest


def _add(admin, code="A-1", name="来客証1"):
    return admin.post("/guest_badges/items/new", data={"code": code, "name": name})


def _lend(admin, code="A-1", no="100001", lent_on=None):
    data = {"item_code": code, "employee_no": no}
    if lent_on is not None:
        data["lent_on"] = lent_on
    return admin.post("/guest_badges/lend", data=data)


def _items(admin):
    return {i["code"]: i for i in admin.get("/guest_badges/status.json").get_json()["items"]}


def _audit(admin):
    rows = admin.get("/audit.json").get_json()["rows"]
    return [(r["action"], r["target"]) for r in rows if r["module"] == "guest_badges"]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_register_and_list(admin):
    r = _add(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/guest_badges/")
    assert "来客証1" in admin.get("/guest_badges/").get_data(as_text=True)
    assert _items(admin)["A-1"]["status"] == "free"
    assert ("item_create", "A-1") in _audit(admin)


def test_duplicate_code_rejected(admin):
    _add(admin)
    r = _add(admin, name="別")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert len(_items(admin)) == 1


def test_edit_and_delete(admin):
    _add(admin)
    assert admin.post("/guest_badges/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert _items(admin)["A-1"]["name"] == "新名"
    assert admin.post("/guest_badges/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400
    assert admin.post("/guest_badges/items/delete", data={"code": "A-1"}).status_code == 302
    assert _items(admin) == {}
    acts = [a for a, _ in _audit(admin)]
    assert "item_update" in acts and "item_delete" in acts


def test_lend_sets_due_one_day_later(admin, emp):
    _add(admin)
    r = _lend(admin)
    assert r.status_code == 302
    item = _items(admin)["A-1"]
    assert (item["status"], item["borrower"], item["lent_on"], item["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-16")
    assert ("lend", "A-1") in _audit(admin)


def test_lend_with_past_date(admin, emp):
    _add(admin)
    assert _lend(admin, lent_on="2026-06-14").status_code == 302
    assert _items(admin)["A-1"]["due_on"] == "2026-06-15"


def test_future_date_rejected(admin, emp):
    _add(admin)
    r = _lend(admin, lent_on="2026-06-16")
    assert r.status_code == 400 and _items(admin)["A-1"]["status"] == "free"
    assert _lend(admin, lent_on="2026-06-15").status_code == 302


def test_bad_date_format_rejected(admin, emp):
    _add(admin)
    assert _lend(admin, lent_on="2026/06/15").status_code == 400
    assert _lend(admin, lent_on="abc").status_code == 400


def test_lent_item_cannot_be_lent_or_deleted(admin, emp, make_employee):
    make_employee("100002", "佐藤")
    _add(admin)
    _lend(admin)
    assert _lend(admin, no="100002").status_code == 400
    r = admin.post("/guest_badges/items/delete", data={"code": "A-1"})
    assert r.status_code == 400 and "A-1" in _items(admin)


def test_limit_three_at_a_time(admin, emp):
    for i in range(1, 5):
        _add(admin, f"A-{i}", f"証{i}")
    for i in range(1, 4):
        assert _lend(admin, f"A-{i}").status_code == 302
    r = _lend(admin, "A-4")
    assert r.status_code == 400 and _items(admin)["A-4"]["status"] == "free"


def test_return_frees_slot_and_keeps_history(admin, emp):
    for i in range(1, 5):
        _add(admin, f"A-{i}", f"証{i}")
    for i in range(1, 4):
        _lend(admin, f"A-{i}")
    assert admin.post("/guest_badges/return", data={"item_code": "A-1"}).status_code == 302
    assert _items(admin)["A-1"]["status"] == "free"
    assert _lend(admin, "A-4").status_code == 302
    page = admin.get("/guest_badges/history")
    assert page.status_code == 200 and "A-1" in page.get_data(as_text=True)
    assert ("return", "A-1") in _audit(admin)


def test_return_not_lent_rejected(admin):
    _add(admin)
    assert admin.post("/guest_badges/return", data={"item_code": "A-1"}).status_code == 400
    assert admin.post("/guest_badges/return", data={"item_code": "Z"}).status_code == 400


def test_due_day_is_not_expired_but_next_day_is(admin, emp, set_today):
    _add(admin, "A-1")
    _add(admin, "A-2")
    _lend(admin, "A-1")  # 期限 2026-06-16
    set_today("2026-06-16")
    assert _items(admin)["A-1"]["status"] == "lent"
    assert _lend(admin, "A-2").status_code == 302
    set_today("2026-06-17")
    assert _items(admin)["A-1"]["status"] == "overdue"


def test_expired_loan_blocks_new_lending(admin, emp, make_employee, set_today):
    make_employee("100002", "佐藤")
    _add(admin, "A-1")
    _add(admin, "A-2")
    _lend(admin, "A-1")
    set_today("2026-06-17")
    r = _lend(admin, "A-2")
    assert r.status_code == 400 and _items(admin)["A-2"]["status"] == "free"
    assert _lend(admin, "A-2", no="100002").status_code == 302  # 他の社員には貸せる
    admin.post("/guest_badges/return", data={"item_code": "A-1"})
    assert _lend(admin, "A-1").status_code == 302  # 返却すれば貸せる


def test_retired_and_unknown_employee_rejected(admin, emp):
    _add(admin)
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert _lend(admin).status_code == 400
    assert _lend(admin, no="999999").status_code == 400
    assert _items(admin)["A-1"]["status"] == "free"


def test_staff_only_for_changes(client, admin, make_employee):
    make_employee("100001", "山田")
    _add(admin)
    admin.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/guest_badges/items/new", data={"code": "B", "name": "x"}).status_code == 403
    assert client.post("/guest_badges/lend", data={"item_code": "A-1", "employee_no": "100001"}).status_code == 403
    assert client.get("/guest_badges/").status_code == 200
    assert client.get("/guest_badges/status.json").status_code == 200


def test_search_filter(admin):
    _add(admin, "A-1", "青い証")
    _add(admin, "B-2", "赤い証")
    page = admin.get("/guest_badges/?q=青").get_data(as_text=True)
    assert "A-1" in page and "B-2" not in page
    page = admin.get("/guest_badges/?q=B-").get_data(as_text=True)
    assert "B-2" in page and "A-1" not in page


def test_status_json_sorted_by_code(admin):
    _add(admin, "B-1", "b")
    _add(admin, "A-1", "a")
    items = admin.get("/guest_badges/status.json").get_json()["items"]
    assert [i["code"] for i in items] == ["A-1", "B-1"]
    assert items[0]["borrower"] is None and items[0]["lent_on"] is None

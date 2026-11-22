"""ホワイトボードの貸出のテスト。きまりを 1 つずつ確かめる（今日は 2026-06-15）。"""

from app.core.db import get_db


def add_item(admin, code="A-1", name="大"):
    r = admin.post("/whiteboards/items/new", data={"code": code, "name": name})
    assert r.status_code == 302, r.get_data(as_text=True)


def lend(admin, code, no, lent_on=None):
    data = {"item_code": code, "employee_no": no}
    if lent_on:
        data["lent_on"] = lent_on
    return admin.post("/whiteboards/lend", data=data)


def status(admin):
    return {i["code"]: i for i in admin.get("/whiteboards/status.json").get_json()["items"]}


def audit_actions(app):
    with app.app_context():
        return [r["action"] for r in get_db().execute("SELECT action FROM audit_log WHERE module='whiteboards' ORDER BY id")]


def test_register_item_and_list(admin):
    add_item(admin)
    body = admin.get("/whiteboards/").get_data(as_text=True)
    assert "A-1" in body and "大" in body


def test_duplicate_code_rejected(admin):
    add_item(admin)
    r = admin.post("/whiteboards/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert status(admin)["A-1"]["name"] == "大"


def test_edit_item_name(admin):
    add_item(admin)
    assert admin.post("/whiteboards/items/edit", data={"code": "A-1", "name": "小"}).status_code == 302
    assert status(admin)["A-1"]["name"] == "小"
    assert admin.post("/whiteboards/items/edit", data={"code": "ZZ", "name": "x"}).status_code == 400


def test_lend_sets_due_date_seven_days(admin, make_employee):
    make_employee("100001")
    add_item(admin)
    assert lend(admin, "A-1", "100001").status_code == 302
    item = status(admin)["A-1"]
    assert (item["status"], item["borrower"], item["lent_on"], item["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-22")


def test_lend_with_explicit_date(admin, make_employee):
    make_employee("100001")
    add_item(admin)
    assert lend(admin, "A-1", "100001", "2026-06-10").status_code == 302
    assert status(admin)["A-1"]["due_on"] == "2026-06-17"


def test_future_date_rejected_but_today_ok(admin, make_employee):
    make_employee("100001")
    add_item(admin)
    assert lend(admin, "A-1", "100001", "2026-06-16").status_code == 400
    assert status(admin)["A-1"]["status"] == "free"
    assert lend(admin, "A-1", "100001", "2026-06-15").status_code == 302
    assert lend(admin, "A-1", "100001", "bad").status_code == 400


def test_lent_item_cannot_be_lent_again(admin, make_employee):
    make_employee("100001")
    make_employee("100002")
    add_item(admin)
    lend(admin, "A-1", "100001")
    r = lend(admin, "A-1", "100002")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert status(admin)["A-1"]["borrower"] == "100001"


def test_limit_two_per_person(admin, make_employee):
    make_employee("100001")
    for c in ("A-1", "A-2", "A-3"):
        add_item(admin, c)
    assert lend(admin, "A-1", "100001").status_code == 302
    assert lend(admin, "A-2", "100001").status_code == 302
    assert lend(admin, "A-3", "100001").status_code == 400
    assert status(admin)["A-3"]["status"] == "free"


def test_return_frees_slot_and_keeps_history(admin, make_employee):
    make_employee("100001")
    for c in ("A-1", "A-2", "A-3"):
        add_item(admin, c)
    lend(admin, "A-1", "100001")
    lend(admin, "A-2", "100001")
    assert admin.post("/whiteboards/return", data={"item_code": "A-1"}).status_code == 302
    assert status(admin)["A-1"]["status"] == "free"
    assert lend(admin, "A-3", "100001").status_code == 302
    history = admin.get("/whiteboards/history").get_data(as_text=True)
    assert "A-1" in history and "100001" in history
    assert admin.post("/whiteboards/return", data={"item_code": "A-1"}).status_code == 400


def test_overdue_boundary(admin, make_employee, set_today):
    make_employee("100001")
    add_item(admin)
    lend(admin, "A-1", "100001")  # 期限 2026-06-22
    set_today("2026-06-22")
    assert status(admin)["A-1"]["status"] == "lent"  # 期限の当日はまだ延滞ではない
    set_today("2026-06-23")
    assert status(admin)["A-1"]["status"] == "overdue"


def test_overdue_borrower_cannot_borrow_more(admin, make_employee, set_today):
    make_employee("100001")
    add_item(admin, "A-1")
    add_item(admin, "A-2")
    lend(admin, "A-1", "100001")
    set_today("2026-06-22")
    assert lend(admin, "A-2", "100001").status_code == 302  # 期限当日は貸せる
    admin.post("/whiteboards/return", data={"item_code": "A-2"})
    set_today("2026-06-23")
    assert lend(admin, "A-2", "100001").status_code == 400
    admin.post("/whiteboards/return", data={"item_code": "A-1"})
    assert lend(admin, "A-2", "100001").status_code == 302


def test_retired_and_unknown_employee_rejected(admin, make_employee):
    make_employee("100001")
    add_item(admin)
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert lend(admin, "A-1", "100001").status_code == 400
    assert lend(admin, "A-1", "999999").status_code == 400
    assert status(admin)["A-1"]["status"] == "free"


def test_cannot_delete_lent_item(admin, make_employee):
    make_employee("100001")
    add_item(admin)
    lend(admin, "A-1", "100001")
    assert admin.post("/whiteboards/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(admin)
    admin.post("/whiteboards/return", data={"item_code": "A-1"})
    assert admin.post("/whiteboards/items/delete", data={"code": "A-1"}).status_code == 302
    assert "A-1" not in status(admin)


def test_search_filter(admin):
    add_item(admin, "A-1", "大きい")
    add_item(admin, "B-2", "小さい")
    body = admin.get("/whiteboards/?q=B-").get_data(as_text=True)
    assert "B-2" in body and "A-1" not in body
    body = admin.get("/whiteboards/?q=大").get_data(as_text=True)
    assert "A-1" in body and "B-2" not in body


def test_status_json_order_and_shape(admin):
    add_item(admin, "B-2")
    add_item(admin, "A-1")
    items = admin.get("/whiteboards/status.json").get_json()["items"]
    assert [i["code"] for i in items] == ["A-1", "B-2"]
    assert items[0] == {"code": "A-1", "name": "大", "status": "free", "borrower": None, "lent_on": None, "due_on": None}


def test_non_staff_cannot_change_data(client, admin, make_employee):
    make_employee("100001")
    add_item(admin)
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.post("/whiteboards/items/new", data={"code": "X", "name": "x"}).status_code == 403
    assert client.post("/whiteboards/lend", data={"item_code": "A-1", "employee_no": "100001"}).status_code == 403
    assert client.get("/whiteboards/status.json").status_code == 200
    assert client.get("/whiteboards/").status_code == 200


def test_audit_records_each_operation(app, admin, make_employee):
    make_employee("100001")
    add_item(admin)
    admin.post("/whiteboards/items/edit", data={"code": "A-1", "name": "小"})
    lend(admin, "A-1", "100001")
    admin.post("/whiteboards/return", data={"item_code": "A-1"})
    admin.post("/whiteboards/items/delete", data={"code": "A-1"})
    lend(admin, "A-1", "100001")  # 失敗した操作は残さない
    assert audit_actions(app) == ["item_create", "item_update", "lend", "return", "item_delete"]

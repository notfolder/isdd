"""プロジェクターの貸出のテスト。"""

import pytest

from app.core.db import get_db


def add_item(admin, code="A-1", name="プロジェクター 1"):
    return admin.post("/projectors/items/new", data={"code": code, "name": name})


def lend(admin, code="A-1", no="100001", lent_on=None):
    data = {"item_code": code, "employee_no": no}
    if lent_on:
        data["lent_on"] = lent_on
    return admin.post("/projectors/lend", data=data)


def status(client):
    return {i["code"]: i for i in client.get("/projectors/status.json").get_json()["items"]}


def audit_rows(app):
    with app.app_context():
        return [tuple(r) for r in get_db().execute("SELECT module, action, target FROM audit_log WHERE module='projectors' ORDER BY id")]


def test_register_and_list(admin):
    r = add_item(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/projectors/")
    html = admin.get("/projectors/").get_data(as_text=True)
    assert "A-1" in html and "プロジェクター 1" in html


def test_duplicate_code_rejected(admin):
    add_item(admin)
    r = add_item(admin, name="別名")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert len(status(admin)) == 1


def test_edit_name(admin):
    add_item(admin)
    r = admin.post("/projectors/items/edit", data={"code": "A-1", "name": "新しい名前"})
    assert r.status_code == 302
    assert status(admin)["A-1"]["name"] == "新しい名前"


def test_employee_cannot_change_data(admin, make_employee, client):
    add_item(admin)
    make_employee("100001")
    admin.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert add_item(client, "B-1").status_code == 403
    assert lend(client).status_code == 403
    assert client.get("/projectors/status.json").status_code == 200


def test_lend_due_is_two_days_later(admin, make_employee):
    add_item(admin)
    make_employee("100001")
    assert lend(admin).status_code == 302
    item = status(admin)["A-1"]
    assert item == {"code": "A-1", "name": "プロジェクター 1", "status": "lent", "borrower": "100001", "lent_on": "2026-06-15", "due_on": "2026-06-17"}


def test_lend_with_past_date(admin, make_employee):
    add_item(admin)
    make_employee("100001")
    assert lend(admin, lent_on="2026-06-14").status_code == 302
    assert status(admin)["A-1"]["due_on"] == "2026-06-16"


def test_future_lent_on_rejected_and_today_accepted(admin, make_employee):
    add_item(admin)
    make_employee("100001")
    assert lend(admin, lent_on="2026-06-16").status_code == 400
    assert status(admin)["A-1"]["status"] == "free"
    assert lend(admin, lent_on="2026-06-15").status_code == 302


def test_invalid_date_rejected(admin, make_employee):
    add_item(admin)
    make_employee("100001")
    assert lend(admin, lent_on="2026/06/15").status_code == 400


def test_lent_item_cannot_be_lent_again(admin, make_employee):
    add_item(admin)
    make_employee("100001")
    make_employee("100002")
    lend(admin)
    assert lend(admin, no="100002").status_code == 400


def test_one_person_one_item_at_a_time(admin, make_employee):
    add_item(admin)
    add_item(admin, "A-2", "プロジェクター 2")
    make_employee("100001")
    lend(admin)
    r = lend(admin, code="A-2")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert status(admin)["A-2"]["status"] == "free"


def test_overdue_boundary(admin, make_employee, set_today):
    add_item(admin)
    make_employee("100001")
    lend(admin)  # 期限は 6/17
    set_today("2026-06-17")
    assert status(admin)["A-1"]["status"] == "lent"
    set_today("2026-06-18")
    assert status(admin)["A-1"]["status"] == "overdue"


def test_overdue_holder_cannot_borrow_new(admin, make_employee, set_today):
    add_item(admin)
    add_item(admin, "A-2", "プロジェクター 2")
    make_employee("100001")
    lend(admin)
    set_today("2026-06-18")
    r = lend(admin, code="A-2")
    assert r.status_code == 400 and "期限" in r.get_data(as_text=True)


def test_can_borrow_again_after_return(admin, make_employee, set_today):
    add_item(admin)
    make_employee("100001")
    lend(admin)
    set_today("2026-06-18")
    assert admin.post("/projectors/return", data={"item_code": "A-1"}).status_code == 302
    assert lend(admin).status_code == 302


def test_retired_and_unknown_employee_rejected(admin, make_employee):
    add_item(admin)
    make_employee("100001")
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert lend(admin).status_code == 400
    assert lend(admin, no="999999").status_code == 400
    assert status(admin)["A-1"]["status"] == "free"


def test_return_keeps_history_newest_first(admin, make_employee, set_today):
    add_item(admin)
    make_employee("100001")
    make_employee("100002", name="二郎")
    lend(admin)
    admin.post("/projectors/return", data={"item_code": "A-1"})
    set_today("2026-06-16")
    lend(admin, no="100002")
    admin.post("/projectors/return", data={"item_code": "A-1"})
    assert status(admin)["A-1"]["status"] == "free"
    html = admin.get("/projectors/history").get_data(as_text=True)
    assert html.index("100002") < html.index("100001")


def test_return_when_not_lent_rejected(admin):
    add_item(admin)
    assert admin.post("/projectors/return", data={"item_code": "A-1"}).status_code == 400


def test_delete_rules(admin, make_employee):
    add_item(admin)
    make_employee("100001")
    lend(admin)
    assert admin.post("/projectors/items/delete", data={"code": "A-1"}).status_code == 400
    admin.post("/projectors/return", data={"item_code": "A-1"})
    assert admin.post("/projectors/items/delete", data={"code": "A-1"}).status_code == 302
    assert status(admin) == {}


def test_search_filter(admin):
    add_item(admin, "A-1", "会議室用")
    add_item(admin, "B-2", "持ち出し用")
    html = admin.get("/projectors/?q=持ち出").get_data(as_text=True)
    assert "B-2" in html and "A-1" not in html
    assert "A-1" in admin.get("/projectors/?q=A-").get_data(as_text=True)


def test_status_json_sorted_by_code(admin):
    add_item(admin, "B-1", "b")
    add_item(admin, "A-1", "a")
    items = admin.get("/projectors/status.json").get_json()["items"]
    assert [i["code"] for i in items] == ["A-1", "B-1"]
    assert items[0]["borrower"] is None and items[0]["due_on"] is None


def test_audit_recorded_and_not_on_rejection(admin, make_employee, app):
    add_item(admin)
    make_employee("100001")
    lend(admin)
    lend(admin, no="999999")
    admin.post("/projectors/return", data={"item_code": "A-1"})
    assert audit_rows(app) == [
        ("projectors", "item_create", "A-1"),
        ("projectors", "lend", "A-1:100001"),
        ("projectors", "return", "A-1"),
    ]

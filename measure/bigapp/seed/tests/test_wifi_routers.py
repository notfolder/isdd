"""モバイル Wi-Fi の貸出のテスト。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/wifi_routers/items/new", data={"code": "A-1", "name": "ルーター1"})
    admin.post("/wifi_routers/items/new", data={"code": "A-2", "name": "ルーター2"})
    return admin


def lend(c, item="A-1", emp="100001", on=None):
    data = {"item_code": item, "employee_no": emp}
    if on:
        data["lent_on"] = on
    return c.post("/wifi_routers/lend", data=data)


def status(c):
    return {i["code"]: i for i in c.get("/wifi_routers/status.json").get_json()["items"]}


def actions(app):
    with app.app_context():
        return [r["action"] for r in get_db().execute("SELECT action FROM audit_log WHERE module = 'wifi_routers' ORDER BY id")]


def test_register_item_and_duplicate(setup, app):
    assert "item_create" in actions(app)
    r = setup.post("/wifi_routers/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert status(setup)["A-1"]["name"] == "ルーター1"


def test_register_requires_code_and_name(setup):
    assert setup.post("/wifi_routers/items/new", data={"code": "", "name": "x"}).status_code == 400
    assert setup.post("/wifi_routers/items/new", data={"code": "B-1", "name": " "}).status_code == 400


def test_edit_item(setup, app):
    r = setup.post("/wifi_routers/items/edit", data={"code": "A-1", "name": "新名"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/wifi_routers/")
    assert status(setup)["A-1"]["name"] == "新名"
    assert "item_update" in actions(app)
    assert setup.post("/wifi_routers/items/edit", data={"code": "ZZ", "name": "x"}).status_code == 400


def test_lend_defaults_today_and_due_5_days(setup, app):
    r = lend(setup)
    assert r.status_code == 302 and r.headers["Location"].endswith("/wifi_routers/")
    s = status(setup)["A-1"]
    assert s == {"code": "A-1", "name": "ルーター1", "status": "lent", "borrower": "100001", "lent_on": "2026-06-15", "due_on": "2026-06-20"}
    assert "lend" in actions(app)


def test_lend_with_date_and_future_rejected(setup):
    assert lend(setup, on="2026-06-15").status_code == 302
    assert status(setup)["A-1"]["due_on"] == "2026-06-20"
    assert lend(setup, "A-2", "100002", on="2026-06-16").status_code == 400
    assert status(setup)["A-2"]["status"] == "free"
    assert lend(setup, "A-2", "100002", on="bad").status_code == 400


def test_one_item_per_employee(setup):
    lend(setup)
    r = lend(setup, "A-2", "100001")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert status(setup)["A-2"]["status"] == "free"


def test_lent_item_cannot_be_lent(setup):
    lend(setup)
    assert lend(setup, "A-1", "100002").status_code == 400
    assert status(setup)["A-1"]["borrower"] == "100001"


def test_overdue_boundary(setup, set_today):
    lend(setup, on="2026-06-15")
    set_today("2026-06-20")
    assert status(setup)["A-1"]["status"] == "lent"
    set_today("2026-06-21")
    assert status(setup)["A-1"]["status"] == "overdue"


def test_overdue_employee_cannot_borrow_and_after_return_can(setup, set_today):
    lend(setup, on="2026-06-10")  # 期限 06-15
    set_today("2026-06-15")
    assert status(setup)["A-1"]["status"] == "lent"
    set_today("2026-06-16")
    assert lend(setup, "A-2", "100001").status_code == 400
    setup.post("/wifi_routers/return", data={"item_code": "A-1"})
    assert lend(setup, "A-2", "100001").status_code == 302


def test_retired_and_unknown_employee(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", "100002").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"


def test_return_and_history(setup, app):
    lend(setup)
    r = setup.post("/wifi_routers/return", data={"item_code": "A-1"})
    assert r.status_code == 302
    assert status(setup)["A-1"]["status"] == "free" and status(setup)["A-1"]["borrower"] is None
    assert "return" in actions(app)
    page = setup.get("/wifi_routers/history").get_data(as_text=True)
    assert "A-1" in page and "2026-06-20" in page
    assert setup.post("/wifi_routers/return", data={"item_code": "A-1"}).status_code == 400


def test_history_newest_first(setup, set_today):
    lend(setup, on="2026-06-01")
    setup.post("/wifi_routers/return", data={"item_code": "A-1"})
    lend(setup, "A-2", "100002", on="2026-06-10")
    setup.post("/wifi_routers/return", data={"item_code": "A-2"})
    page = setup.get("/wifi_routers/history").get_data(as_text=True)
    assert page.index("A-2") < page.index("A-1")


def test_delete_rules(setup, app):
    lend(setup)
    assert setup.post("/wifi_routers/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(setup)
    r = setup.post("/wifi_routers/items/delete", data={"code": "A-2"})
    assert r.status_code == 302 and "A-2" not in status(setup)
    assert "item_delete" in actions(app)


def test_staff_only_posts(setup, client, make_employee):
    c = client.application.test_client()
    c.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert c.post("/wifi_routers/lend", data={"item_code": "A-1", "employee_no": "100001"}).status_code == 403
    assert c.post("/wifi_routers/items/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert c.get("/wifi_routers/status.json").status_code == 200
    assert "A-1" not in str(status(setup)) or status(setup)["A-1"]["status"] == "free"


def test_list_search_and_status_sorted(setup):
    page = setup.get("/wifi_routers/?q=ルーター2").get_data(as_text=True)
    assert "A-2" in page and "A-1" not in page
    assert list(status(setup)) == ["A-1", "A-2"]

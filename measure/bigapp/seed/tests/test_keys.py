"""鍵の貸出のテスト。きまりを 1 つずつ確かめる。今日は conftest で 2026-06-15。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    for code in ("A-1", "A-2", "A-3"):
        assert admin.post("/keys/items/new", data={"code": code, "name": f"鍵{code}"}).status_code == 302
    return admin


def lend(c, item, no, on=None):
    data = {"item_code": item, "employee_no": no}
    if on:
        data["lent_on"] = on
    return c.post("/keys/lend", data=data)


def status(c):
    return {i["code"]: i for i in c.get("/keys/status.json").get_json()["items"]}


def assert_rejected(response, c=None):
    assert response.status_code == 400
    assert '<p class="error">' in response.get_data(as_text=True)


def test_item_create_edit_delete(setup):
    c = setup
    assert_rejected(c.post("/keys/items/new", data={"code": "A-1", "name": "重複"}))
    assert_rejected(c.post("/keys/items/new", data={"code": "", "name": "x"}))
    assert c.post("/keys/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert status(c)["A-1"]["name"] == "新名"
    assert_rejected(c.post("/keys/items/edit", data={"code": "Z-9", "name": "x"}))
    assert c.post("/keys/items/delete", data={"code": "A-3"}).status_code == 302
    assert "A-3" not in status(c)
    assert_rejected(c.post("/keys/items/delete", data={"code": "A-3"}))


def test_lend_sets_due_one_day_later(setup):
    c = setup
    r = lend(c, "A-1", "100001")
    assert r.status_code == 302 and r.headers["Location"].endswith("/keys/")
    s = status(c)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-16")


def test_lend_with_date_and_month_boundary(setup):
    c = setup
    assert lend(c, "A-1", "100001", "2026-06-14").status_code == 302
    s = status(c)["A-1"]
    assert (s["lent_on"], s["due_on"]) == ("2026-06-14", "2026-06-15")
    # 期限が今日なら延滞ではない（今日 > 期限 のときだけ延滞）
    assert s["status"] == "lent"


def test_future_and_bad_date_rejected(setup):
    c = setup
    assert lend(c, "A-1", "100001", "2026-06-15").status_code == 302
    assert_rejected(lend(c, "A-2", "100001", "2026-06-16"))
    assert_rejected(lend(c, "A-2", "100001", "2026/06/14"))
    assert status(c)["A-2"]["status"] == "free"


def test_item_already_lent_cannot_be_lent(setup):
    c = setup
    lend(c, "A-1", "100001")
    assert_rejected(lend(c, "A-1", "100002"))
    assert status(c)["A-1"]["borrower"] == "100001"


def test_limit_two_per_person(setup):
    c = setup
    assert lend(c, "A-1", "100001").status_code == 302
    assert lend(c, "A-2", "100001").status_code == 302
    assert_rejected(lend(c, "A-3", "100001"))
    assert lend(c, "A-3", "100002").status_code == 302  # 別の人は借りられる


def test_limit_frees_after_return(setup):
    c = setup
    lend(c, "A-1", "100001")
    lend(c, "A-2", "100001")
    assert c.post("/keys/return", data={"item_code": "A-1"}).status_code == 302
    assert lend(c, "A-3", "100001").status_code == 302


def test_overdue_holder_cannot_borrow(setup, set_today):
    c = setup
    lend(c, "A-1", "100001")  # 期限 06-16
    set_today("2026-06-16")  # 期限当日は延滞ではない
    assert status(c)["A-1"]["status"] == "lent"
    assert lend(c, "A-2", "100001").status_code == 302
    set_today("2026-06-17")  # 翌日から延滞（A-1 も A-2 も）
    assert status(c)["A-1"]["status"] == "overdue"
    assert_rejected(lend(c, "A-3", "100001"))
    assert lend(c, "A-3", "100002").status_code == 302  # 他の人には貸せる


def test_overdue_cleared_after_return(setup, set_today):
    c = setup
    lend(c, "A-1", "100001")
    set_today("2026-06-20")
    assert_rejected(lend(c, "A-2", "100001"))
    assert c.post("/keys/return", data={"item_code": "A-1"}).status_code == 302
    assert lend(c, "A-2", "100001").status_code == 302


def test_cannot_delete_lent_item(setup):
    c = setup
    lend(c, "A-1", "100001")
    assert_rejected(c.post("/keys/items/delete", data={"code": "A-1"}))
    assert "A-1" in status(c)
    c.post("/keys/return", data={"item_code": "A-1"})
    assert c.post("/keys/items/delete", data={"code": "A-1"}).status_code == 302


def test_return_rules_and_history(setup, set_today):
    c = setup
    assert_rejected(c.post("/keys/return", data={"item_code": "A-1"}))  # 貸出中でない
    lend(c, "A-1", "100001")
    set_today("2026-06-16")
    assert c.post("/keys/return", data={"item_code": "A-1"}).status_code == 302
    assert status(c)["A-1"]["status"] == "free"
    assert status(c)["A-1"]["borrower"] is None
    html = c.get("/keys/history").get_data(as_text=True)
    assert "A-1" in html and "2026-06-15" in html and "2026-06-16" in html


def test_history_newest_first(setup, set_today):
    c = setup
    lend(c, "A-1", "100001")
    c.post("/keys/return", data={"item_code": "A-1"})
    set_today("2026-06-16")
    lend(c, "A-2", "100002")
    c.post("/keys/return", data={"item_code": "A-2"})
    html = c.get("/keys/history").get_data(as_text=True)
    assert html.index("A-2") < html.index("A-1")


def test_retired_and_unknown_employee_rejected(setup):
    c = setup
    c.post("/employees/retire", data={"employee_no": "100002"})
    assert_rejected(lend(c, "A-1", "100002"))
    assert_rejected(lend(c, "A-1", "999999"))
    assert_rejected(lend(c, "Z-9", "100001"))
    assert status(c)["A-1"]["status"] == "free"


def test_staff_only_for_post(setup, client, make_employee):
    make_employee("100003", "一般")
    client.post("/login", data={"employee_no": "100003", "password": "password1"})
    assert client.post("/keys/items/new", data={"code": "B-1", "name": "x"}).status_code == 403
    assert lend(client, "A-1", "100003").status_code == 403
    assert client.post("/keys/return", data={"item_code": "A-1"}).status_code == 403
    assert client.get("/keys/status.json").status_code == 200  # 見るのは誰でも
    assert "B-1" not in status(client)


def test_login_required(app):
    c = app.test_client()
    assert c.get("/keys/status.json").status_code == 302
    assert c.post("/keys/lend", data={}).status_code == 302


def test_status_json_order_and_overdue(setup, set_today):
    c = setup
    lend(c, "A-2", "100001")
    set_today("2026-06-17")
    items = c.get("/keys/status.json").get_json()["items"]
    assert [i["code"] for i in items] == ["A-1", "A-2", "A-3"]
    assert items[0] == {"code": "A-1", "name": "鍵A-1", "status": "free", "borrower": None, "lent_on": None, "due_on": None}
    assert items[1]["status"] == "overdue"


def test_index_search(setup):
    c = setup
    html = c.get("/keys/?q=A-2").get_data(as_text=True)
    assert "A-2" in html and "A-1" not in html
    assert "鍵A-3" in c.get("/keys/?q=鍵A-3").get_data(as_text=True)


def test_audit_records(setup, admin):
    c = setup
    lend(c, "A-1", "100001")
    c.post("/keys/return", data={"item_code": "A-1"})
    c.post("/keys/items/edit", data={"code": "A-1", "name": "n"})
    c.post("/keys/items/delete", data={"code": "A-1"})
    lend(c, "Z-9", "100001")  # 失敗は残さない
    rows = c.get("/audit.json").get_json()["rows"]
    actions = [r["action"] for r in rows if r["module"] == "keys"]
    assert actions == ["item_create"] * 3 + ["lend", "return", "item_update", "item_delete"]
    assert [r["target"] for r in rows if r["action"] == "lend"] == ["A-1"]

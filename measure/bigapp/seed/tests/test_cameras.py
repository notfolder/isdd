"""カメラの貸出のテスト。きまりを 1 つずつ確かめる。"""

import pytest


@pytest.fixture
def cam(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    admin.post("/cameras/items/new", data={"code": "A-1", "name": "一眼"})
    admin.post("/cameras/items/new", data={"code": "A-2", "name": "コンパクト"})
    return admin


def lend(c, item="A-1", emp="100001", **kw):
    return c.post("/cameras/lend", data={"item_code": item, "employee_no": emp, **kw})


def status(c):
    return {i["code"]: i for i in c.get("/cameras/status.json").get_json()["items"]}


def audit_actions(c):
    return [r["action"] for r in c.get("/audit.json").get_json()["rows"] if r["module"] == "cameras"]


def test_register_item(cam):
    r = cam.post("/cameras/items/new", data={"code": "B-1", "name": "新品"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/cameras/")
    assert status(cam)["B-1"]["status"] == "free"
    assert "item_create" in audit_actions(cam)


def test_duplicate_code_rejected(cam):
    r = cam.post("/cameras/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert status(cam)["A-1"]["name"] == "一眼"


def test_empty_code_or_name_rejected(cam):
    assert cam.post("/cameras/items/new", data={"code": "", "name": "x"}).status_code == 400
    assert cam.post("/cameras/items/new", data={"code": "C", "name": " "}).status_code == 400


def test_edit_item(cam):
    assert cam.post("/cameras/items/edit", data={"code": "A-1", "name": "改名"}).status_code == 302
    assert status(cam)["A-1"]["name"] == "改名"
    assert cam.post("/cameras/items/edit", data={"code": "Z-9", "name": "x"}).status_code == 400
    assert "item_update" in audit_actions(cam)


def test_delete_item_and_lent_item_protected(cam):
    lend(cam)
    r = cam.post("/cameras/items/delete", data={"code": "A-1"})
    assert r.status_code == 400 and "A-1" in status(cam)
    assert cam.post("/cameras/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(cam)
    assert "item_delete" in audit_actions(cam)


def test_lend_due_is_five_days(cam):
    assert lend(cam).status_code == 302
    s = status(cam)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-20")
    assert "lend" in audit_actions(cam)


def test_lend_with_past_date(cam):
    assert lend(cam, lent_on="2026-06-14").status_code == 302
    assert status(cam)["A-1"]["due_on"] == "2026-06-19"


def test_future_lent_on_rejected(cam):
    assert lend(cam, lent_on="2026-06-16").status_code == 400
    assert status(cam)["A-1"]["status"] == "free"
    assert lend(cam, lent_on="2026-06-15").status_code == 302


def test_bad_date_rejected(cam):
    assert lend(cam, lent_on="abc").status_code == 400


def test_one_item_per_person(cam):
    lend(cam)
    r = lend(cam, item="A-2")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert lend(cam, item="A-2", emp="100002").status_code == 302


def test_cannot_lend_lent_item(cam):
    lend(cam)
    assert lend(cam, emp="100002").status_code == 400


def test_overdue_boundary(cam, set_today):
    lend(cam)  # 期限 2026-06-20
    set_today("2026-06-20")
    assert status(cam)["A-1"]["status"] == "lent"
    set_today("2026-06-21")
    assert status(cam)["A-1"]["status"] == "overdue"


def test_overdue_holder_cannot_borrow_after_return_ok(cam, set_today):
    lend(cam)
    set_today("2026-06-21")
    assert lend(cam, item="A-2").status_code == 400
    cam.post("/cameras/return", data={"item_code": "A-1"})
    assert lend(cam, item="A-2").status_code == 302


def test_return_and_history(cam):
    lend(cam)
    assert cam.post("/cameras/return", data={"item_code": "A-1"}).status_code == 302
    assert status(cam)["A-1"]["status"] == "free"
    page = cam.get("/cameras/history").get_data(as_text=True)
    assert "A-1" in page and "100001" in page and "2026-06-15" in page
    assert "return" in audit_actions(cam)
    assert cam.post("/cameras/return", data={"item_code": "A-1"}).status_code == 400


def test_history_newest_first(cam, set_today):
    lend(cam, item="A-1", emp="100001")
    cam.post("/cameras/return", data={"item_code": "A-1"})
    set_today("2026-06-16")
    lend(cam, item="A-2", emp="100002")
    cam.post("/cameras/return", data={"item_code": "A-2"})
    page = cam.get("/cameras/history").get_data(as_text=True)
    assert page.index("A-2") < page.index("A-1")


def test_retired_and_unknown_employee_rejected(cam):
    cam.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(cam, emp="100002").status_code == 400
    assert lend(cam, emp="999999").status_code == 400
    assert lend(cam, item="NOPE").status_code == 400


def test_search(cam):
    page = cam.get("/cameras/?q=コンパ").get_data(as_text=True)
    assert "A-2" in page and "A-1" not in page
    assert "A-1" in cam.get("/cameras/?q=A-1").get_data(as_text=True)


def test_rejected_changes_nothing_and_no_audit(cam):
    before = audit_actions(cam)
    lend(cam, emp="999999")
    assert audit_actions(cam) == before


def test_employee_cannot_post_but_can_view(app, cam, make_employee):
    c = app.test_client()
    c.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert c.post("/cameras/items/new", data={"code": "X", "name": "x"}).status_code == 403
    assert c.get("/cameras/").status_code == 200
    assert c.get("/cameras/status.json").status_code == 200


def test_status_json_order_and_shape(cam):
    items = cam.get("/cameras/status.json").get_json()["items"]
    assert [i["code"] for i in items] == ["A-1", "A-2"]
    assert items[0] == {"code": "A-1", "name": "一眼", "status": "free", "borrower": None, "lent_on": None, "due_on": None}

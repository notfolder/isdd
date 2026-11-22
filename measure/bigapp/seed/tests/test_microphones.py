"""マイクの貸出のテスト。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def mics(admin, make_employee):
    """マイク A-1〜A-5 と、在籍の社員 100001 を用意する。"""
    make_employee("100001", "山田")
    for n in range(1, 6):
        admin.post("/microphones/items/new", data={"code": f"A-{n}", "name": f"マイク{n}"})
    return admin


def lend(c, code, no="100001", on=None):
    data = {"item_code": code, "employee_no": no}
    if on:
        data["lent_on"] = on
    return c.post("/microphones/lend", data=data)


def status(c):
    return {i["code"]: i for i in c.get("/microphones/status.json").get_json()["items"]}


def audit_rows(app):
    with app.app_context():
        return [(r["module"], r["action"], r["target"]) for r in get_db().execute("SELECT * FROM audit_log ORDER BY id")]


def test_register_item_and_audit(app, mics):
    assert audit_rows(app)[-1] == ("microphones", "item_create", "A-5")
    assert "マイク1" in mics.get("/microphones/").get_data(as_text=True)


def test_duplicate_code_rejected(mics):
    r = mics.post("/microphones/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert status(mics)["A-1"]["name"] == "マイク1"


def test_edit_item_name(app, mics):
    r = mics.post("/microphones/items/edit", data={"code": "A-1", "name": "新名"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/microphones/")
    assert status(mics)["A-1"]["name"] == "新名"
    assert audit_rows(app)[-1] == ("microphones", "item_update", "A-1")
    assert mics.post("/microphones/items/edit", data={"code": "ZZ", "name": "x"}).status_code == 400


def test_lend_sets_due_three_days_later(app, mics):
    r = lend(mics, "A-1")
    assert r.status_code == 302
    s = status(mics)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-06-18")
    assert audit_rows(app)[-1] == ("microphones", "lend", "A-1")


def test_lend_with_past_date(mics):
    lend(mics, "A-1", on="2026-06-10")
    s = status(mics)["A-1"]
    assert (s["lent_on"], s["due_on"]) == ("2026-06-10", "2026-06-13")


def test_future_lent_on_rejected_today_ok(mics):
    assert lend(mics, "A-1", on="2026-06-16").status_code == 400
    assert status(mics)["A-1"]["status"] == "free"
    assert lend(mics, "A-1", on="2026-06-15").status_code == 302


def test_bad_date_format_rejected(mics):
    assert lend(mics, "A-1", on="2026/06/10").status_code == 400
    assert lend(mics, "A-1", on="abc").status_code == 400


def test_cannot_lend_lent_item(make_employee, mics):
    make_employee("100002", "佐藤")
    lend(mics, "A-1")
    r = lend(mics, "A-1", no="100002")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert status(mics)["A-1"]["borrower"] == "100001"


def test_limit_three_at_once(mics):
    for c in ("A-1", "A-2", "A-3"):
        assert lend(mics, c).status_code == 302
    assert lend(mics, "A-4").status_code == 400
    assert status(mics)["A-4"]["status"] == "free"


def test_fourth_ok_after_return(mics):
    for c in ("A-1", "A-2", "A-3"):
        lend(mics, c)
    mics.post("/microphones/return", data={"item_code": "A-1"})
    assert lend(mics, "A-4").status_code == 302


def test_due_day_is_not_overdue_next_day_is(set_today, mics):
    lend(mics, "A-1")  # 期限 2026-06-18
    set_today("2026-06-18")
    assert status(mics)["A-1"]["status"] == "lent"
    set_today("2026-06-19")
    assert status(mics)["A-1"]["status"] == "overdue"


def test_overdue_holder_cannot_borrow_more(set_today, mics):
    lend(mics, "A-1")
    set_today("2026-06-18")
    assert lend(mics, "A-2").status_code == 302  # 期限当日は延滞ではない
    set_today("2026-06-19")
    r = lend(mics, "A-3")
    assert r.status_code == 400
    assert status(mics)["A-3"]["status"] == "free"


def test_other_employee_unaffected_by_overdue(set_today, make_employee, mics):
    make_employee("100002", "佐藤")
    lend(mics, "A-1")
    set_today("2026-06-19")
    assert lend(mics, "A-2", no="100002").status_code == 302


def test_overdue_cleared_after_return(set_today, mics):
    lend(mics, "A-1")
    set_today("2026-06-19")
    mics.post("/microphones/return", data={"item_code": "A-1"})
    assert lend(mics, "A-2").status_code == 302


def test_retired_and_unknown_employee_rejected(make_employee, mics):
    make_employee("100003", "退職者")
    mics.post("/employees/retire", data={"employee_no": "100003"})
    assert lend(mics, "A-1", no="100003").status_code == 400
    assert lend(mics, "A-1", no="999999").status_code == 400
    assert status(mics)["A-1"]["status"] == "free"


def test_return_and_history(app, mics):
    lend(mics, "A-1", on="2026-06-14")
    r = mics.post("/microphones/return", data={"item_code": "A-1"})
    assert r.status_code == 302
    s = status(mics)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("free", None, None, None)
    assert audit_rows(app)[-1] == ("microphones", "return", "A-1")
    body = mics.get("/microphones/history").get_data(as_text=True)
    assert "A-1" in body and "2026-06-14" in body
    assert mics.post("/microphones/return", data={"item_code": "A-1"}).status_code == 400


def test_history_newest_first(set_today, mics):
    lend(mics, "A-1")
    mics.post("/microphones/return", data={"item_code": "A-1"})
    set_today("2026-06-16")
    lend(mics, "A-2")
    mics.post("/microphones/return", data={"item_code": "A-2"})
    body = mics.get("/microphones/history").get_data(as_text=True)
    assert body.index("A-2") < body.index("A-1")


def test_delete_item(app, mics):
    assert mics.post("/microphones/items/delete", data={"code": "A-5"}).status_code == 302
    assert "A-5" not in status(mics)
    assert audit_rows(app)[-1] == ("microphones", "item_delete", "A-5")


def test_cannot_delete_lent_item(mics):
    lend(mics, "A-1")
    r = mics.post("/microphones/items/delete", data={"code": "A-1"})
    assert r.status_code == 400
    assert "A-1" in status(mics)


def test_search_filter(mics):
    body = mics.get("/microphones/?q=マイク3").get_data(as_text=True)
    assert "A-3" in body and "A-2" not in body
    assert "A-4" in mics.get("/microphones/?q=A-4").get_data(as_text=True)


def test_status_json_sorted_and_visible_to_employee(client, mics, make_employee):
    codes = [i["code"] for i in mics.get("/microphones/status.json").get_json()["items"]]
    assert codes == sorted(codes)
    mics.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.get("/microphones/status.json").status_code == 200


def test_non_staff_cannot_post_and_failure_not_audited(app, client, mics):
    before = len(audit_rows(app))
    lend(mics, "A-1", no="999999")
    assert len(audit_rows(app)) == before
    mics.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert lend(client, "A-1").status_code == 403
    assert client.post("/microphones/items/new", data={"code": "B", "name": "b"}).status_code == 403

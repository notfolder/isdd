"""モバイル機器の貸出のテスト。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def setup(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤")
    for code in ("A-1", "A-2", "B-1"):
        assert admin.post("/devices/items/new", data={"code": code, "name": f"端末{code}"}).status_code == 302
    return admin


def lend(c, item="A-1", emp="100001", on=None):
    data = {"item_code": item, "employee_no": emp}
    if on:
        data["lent_on"] = on
    return c.post("/devices/lend", data=data)


def status(c):
    return {i["code"]: i for i in c.get("/devices/status.json").get_json()["items"]}


def test_登録は一覧に出て302(setup):
    r = setup.get("/devices/")
    assert "A-1" in r.get_data(as_text=True)
    assert list(status(setup)) == ["A-1", "A-2", "B-1"]


def test_番号の重複は400(setup):
    r = setup.post("/devices/items/new", data={"code": "A-1", "name": "別"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert len(status(setup)) == 3


def test_名前を直す(setup):
    assert setup.post("/devices/items/edit", data={"code": "A-1", "name": "新名"}).status_code == 302
    assert status(setup)["A-1"]["name"] == "新名"
    assert setup.post("/devices/items/edit", data={"code": "ZZ", "name": "x"}).status_code == 400


def test_期限は貸出日の30日後(setup):
    assert lend(setup).status_code == 302
    s = status(setup)["A-1"]
    assert (s["status"], s["borrower"], s["lent_on"], s["due_on"]) == ("lent", "100001", "2026-06-15", "2026-07-15")


def test_貸出日の指定と未来の日付(setup):
    assert lend(setup, on="2026-06-15").status_code == 302
    assert lend(setup, "A-2", "100002", "2026-06-16").status_code == 400
    assert lend(setup, "A-2", "100002", "2026-05-01").status_code == 302
    assert status(setup)["A-2"]["due_on"] == "2026-05-31"
    assert lend(setup, "B-1", "100001", "abc").status_code == 400


def test_1人1件まで(setup):
    assert lend(setup).status_code == 302
    r = lend(setup, "A-2")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert status(setup)["A-2"]["status"] == "free"


def test_貸出中の物は貸せない(setup):
    lend(setup)
    assert lend(setup, "A-1", "100002").status_code == 400


def test_期限当日は延滞でなく翌日から延滞(setup, set_today):
    lend(setup)  # 期限 2026-07-15
    set_today("2026-07-15")
    assert status(setup)["A-1"]["status"] == "lent"
    set_today("2026-07-16")
    assert status(setup)["A-1"]["status"] == "overdue"


def test_延滞中の社員には貸さない(setup, set_today):
    lend(setup)
    set_today("2026-07-16")
    assert lend(setup, "A-2").status_code == 400
    setup.post("/devices/return", data={"item_code": "A-1"})
    assert lend(setup, "A-2").status_code == 302


def test_期限当日の社員は返却前でも1件制限で400(setup, set_today):
    lend(setup)
    set_today("2026-07-15")
    assert lend(setup, "A-2").status_code == 400


def test_退職者と存在しない社員は400(setup):
    setup.post("/employees/retire", data={"employee_no": "100002"})
    assert lend(setup, "A-1", "100002").status_code == 400
    assert lend(setup, "A-1", "999999").status_code == 400
    assert status(setup)["A-1"]["status"] == "free"


def test_返却と履歴(setup, set_today):
    lend(setup)
    set_today("2026-06-20")
    assert setup.post("/devices/return", data={"item_code": "A-1"}).status_code == 302
    assert status(setup)["A-1"]["status"] == "free"
    text = setup.get("/devices/history").get_data(as_text=True)
    assert "A-1" in text and "2026-06-20" in text
    assert setup.post("/devices/return", data={"item_code": "A-1"}).status_code == 400


def test_貸出中は削除できない(setup):
    lend(setup)
    assert setup.post("/devices/items/delete", data={"code": "A-1"}).status_code == 400
    assert "A-1" in status(setup)
    assert setup.post("/devices/items/delete", data={"code": "A-2"}).status_code == 302
    assert "A-2" not in status(setup)


def test_絞り込み(setup):
    text = setup.get("/devices/?q=B-1").get_data(as_text=True)
    assert "B-1" in text and "A-2" not in text


def test_社員は操作できず閲覧はできる(app, setup, make_employee):
    make_employee("100003", "田中")
    c = app.test_client()
    c.post("/login", data={"employee_no": "100003", "password": "password1"})
    assert c.post("/devices/lend", data={"item_code": "A-1", "employee_no": "100003"}).status_code == 403
    assert c.post("/devices/items/new", data={"code": "Z", "name": "z"}).status_code == 403
    assert c.get("/devices/status.json").status_code == 200
    assert c.get("/devices/").status_code == 200


def test_操作の記録が残る(app, setup):
    lend(setup)
    setup.post("/devices/return", data={"item_code": "A-1"})
    setup.post("/devices/items/edit", data={"code": "A-2", "name": "n"})
    setup.post("/devices/items/delete", data={"code": "A-2"})
    lend(setup, "A-1", "100001", "2099-01-01")  # 失敗は残さない
    with app.app_context():
        rows = get_db().execute("SELECT action FROM audit_log WHERE module = 'devices' ORDER BY id").fetchall()
    actions = [r["action"] for r in rows]
    assert actions == ["item_create"] * 3 + ["lend", "return", "item_update", "item_delete"]

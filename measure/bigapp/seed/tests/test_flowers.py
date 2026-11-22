"""生花の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO


def apply(client, no="100001", q="3", p="333"):
    return client.post("/flowers/apply", data={"employee_no": no, "quantity": q, "unit_price": p})


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def rows(client):
    return client.get("/flowers/status.json").get_json()["requests"]


def audit_actions(client):
    return [(r["module"], r["action"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "flowers"]


def login(client, no):
    client.post("/logout")
    client.post("/login", data={"employee_no": no, "password": "password1"})


def test_apply_success(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/flowers/")
    assert rows(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]


def test_tax_rounds_down(admin, emp):
    apply(admin, q="1", p="1")  # 1.1 -> 1
    apply(admin, q="3", p="5")  # 16.5 -> 16
    apply(admin, q="10", p="100000")  # 1100000
    assert [r["amount_incl_tax"] for r in rows(admin)] == [1, 16, 1100000]


@pytest.mark.parametrize("q", ["0", "11", "-1", "abc", "", "1.5"])
def test_quantity_rejected(admin, emp, q):
    r = apply(admin, q=q)
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin) == []


@pytest.mark.parametrize("q", ["1", "10"])
def test_quantity_boundary_ok(admin, emp, q):
    assert apply(admin, q=q).status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "-5", "x", ""])
def test_unit_price_rejected(admin, emp, p):
    assert apply(admin, p=p).status_code == 400
    assert rows(admin) == []


@pytest.mark.parametrize("p", ["1", "100000"])
def test_unit_price_boundary_ok(admin, emp, p):
    assert apply(admin, p=p).status_code == 302


def test_retired_and_unknown_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert apply(admin, no="999999").status_code == 400
    assert rows(admin) == []


def test_only_staff_can_post(admin, make_employee):
    make_employee("100002", "佐藤")
    apply(admin, no="100002")
    login(admin, "100002")
    assert apply(admin, no="100002").status_code == 403
    assert admin.post("/flowers/approve", data={"request_id": "1"}).status_code == 403
    assert admin.post("/flowers/reject", data={"request_id": "1"}).status_code == 403
    assert rows(admin)[0]["state"] == "pending"


def test_approve_and_reject(admin, emp):
    apply(admin)
    apply(admin)
    assert admin.post("/flowers/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/flowers/reject", data={"request_id": "2"}).status_code == 302
    assert [r["state"] for r in rows(admin)] == ["approved", "rejected"]


def test_cannot_decide_twice(admin, emp):
    apply(admin)
    admin.post("/flowers/approve", data={"request_id": "1"})
    for action in ("approve", "reject"):
        r = admin.post(f"/flowers/{action}", data={"request_id": "1"})
        assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "approved"


def test_unknown_request_rejected(admin, emp):
    assert admin.post("/flowers/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/flowers/reject", data={"request_id": "abc"}).status_code == 400


def test_cannot_approve_own_but_can_reject(admin):
    apply(admin, no=ADMIN_NO)
    apply(admin, no=ADMIN_NO)
    r = admin.post("/flowers/approve", data={"request_id": "1"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"
    assert admin.post("/flowers/reject", data={"request_id": "2"}).status_code == 302
    assert rows(admin)[1]["state"] == "rejected"


def test_other_staff_can_approve(admin, make_employee):
    make_employee("100003", "総務二", role="staff")
    apply(admin, no="100003")
    assert admin.post("/flowers/approve", data={"request_id": "1"}).status_code == 302


def test_state_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, q="2", p="500")
    admin.post("/flowers/approve", data={"request_id": "1"})
    html = admin.get("/flowers/?state=approved").get_data(as_text=True)
    assert 'data-request-id="1"' in html and 'data-request-id="2"' not in html
    d = admin.get("/flowers/detail?request_id=2")
    text = d.get_data(as_text=True)
    assert d.status_code == 200 and "1100" in text and "1000" in text and "申請中" in text and "山田" in text
    assert admin.get("/flowers/detail?request_id=9").status_code == 404


def test_audit_records(admin, emp):
    apply(admin)
    apply(admin, q="0")  # 失敗は残さない
    admin.post("/flowers/approve", data={"request_id": "1"})
    apply(admin)
    admin.post("/flowers/reject", data={"request_id": "2"})
    assert audit_actions(admin) == [("flowers", "apply"), ("flowers", "approve"), ("flowers", "apply"), ("flowers", "reject")]


def test_status_json_visible_to_employee_and_login_required(admin, emp, client):
    apply(admin)
    login(admin, "100001")
    assert len(rows(admin)) == 1
    admin.post("/logout")
    assert admin.get("/flowers/status.json").status_code == 302

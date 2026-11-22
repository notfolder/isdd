"""トナーの申請のテスト。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def apply(client, no="100001", q="3", p="333"):
    return client.post("/toner/apply", data={"employee_no": no, "quantity": q, "unit_price": p})


def rows(client):
    return client.get("/toner/status.json").get_json()["requests"]


def test_apply_success_redirects(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/toner/")
    assert rows(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]


def test_tax_rounds_down(admin, emp):
    apply(admin, q="1", p="1")  # 1.1 -> 1
    apply(admin, q="1", p="19")  # 20.9 -> 20
    apply(admin, q="3", p="333")  # 1098.9 -> 1098
    assert [x["amount_incl_tax"] for x in rows(admin)] == [1, 20, 1098]


def test_tax_max(admin, emp):
    apply(admin, q="10", p="100000")
    assert rows(admin)[0]["amount_incl_tax"] == 1100000


@pytest.mark.parametrize("q", ["1", "10"])
def test_quantity_boundary_ok(admin, emp, q):
    assert apply(admin, q=q).status_code == 302


@pytest.mark.parametrize("q", ["0", "11", "-1", "1.5", "", "abc"])
def test_quantity_invalid(admin, emp, q):
    r = apply(admin, q=q)
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin) == []


@pytest.mark.parametrize("p", ["1", "100000"])
def test_price_boundary_ok(admin, emp, p):
    assert apply(admin, p=p).status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "-5", "9.9", "", "x"])
def test_price_invalid(admin, emp, p):
    assert apply(admin, p=p).status_code == 400
    assert rows(admin) == []


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert rows(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, no="999999").status_code == 400


def test_non_staff_cannot_post(client, admin, make_employee):
    make_employee("100002", "社員")
    client.post("/logout")
    client.post("/login", data={"employee_no": "100002", "password": "password1"})
    assert apply(client, no="100002").status_code == 403
    assert client.post("/toner/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/toner/reject", data={"request_id": "1"}).status_code == 403


def test_approve_by_other_staff(admin, make_employee):
    make_employee("100003", "担当", role="staff")
    apply(admin, no="100003")
    r = admin.post("/toner/approve", data={"request_id": "1"})
    assert r.status_code == 302
    assert rows(admin)[0]["state"] == "approved"


def test_self_approval_rejected_but_reject_allowed(admin):
    apply(admin, no="900001")
    r = admin.post("/toner/approve", data={"request_id": "1"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"
    assert admin.post("/toner/reject", data={"request_id": "1"}).status_code == 302
    assert rows(admin)[0]["state"] == "rejected"


def test_only_pending_can_be_decided(admin, emp):
    apply(admin)
    admin.post("/toner/approve", data={"request_id": "1"})
    assert admin.post("/toner/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/toner/reject", data={"request_id": "1"}).status_code == 400
    apply(admin)
    admin.post("/toner/reject", data={"request_id": "2"})
    assert admin.post("/toner/approve", data={"request_id": "2"}).status_code == 400
    assert rows(admin)[1]["state"] == "rejected"


def test_unknown_request_id(admin):
    assert admin.post("/toner/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/toner/reject", data={"request_id": "abc"}).status_code == 400


def test_state_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, q="2", p="100")
    admin.post("/toner/approve", data={"request_id": "1"})
    html = admin.get("/toner/?state=approved").get_data(as_text=True)
    assert 'data-request-id="1"' in html and 'data-request-id="2"' not in html
    assert admin.get("/toner/?state=bogus").status_code == 400
    d = admin.get("/toner/detail?request_id=2").get_data(as_text=True)
    assert "220" in d and "100" in d and "100001" in d
    assert admin.get("/toner/detail?request_id=9").status_code == 404


def test_audit_recorded_only_on_success(admin, emp):
    apply(admin)
    apply(admin, q="0")
    admin.post("/toner/approve", data={"request_id": "1"})
    admin.post("/toner/reject", data={"request_id": "1"})  # 失敗
    apply(admin)
    admin.post("/toner/reject", data={"request_id": "2"})
    log = [(r["module"], r["action"], r["target"]) for r in admin.get("/audit.json").get_json()["rows"] if r["module"] == "toner"]
    assert log == [("toner", "apply", "1"), ("toner", "approve", "1"), ("toner", "apply", "2"), ("toner", "reject", "2")]


def test_login_required(client):
    assert client.get("/toner/status.json").status_code == 302
    assert client.get("/toner/").status_code == 302

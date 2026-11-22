"""贈答品の申請のテスト。"""

import pytest

from app.core.db import get_db


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def apply(client, no="100001", quantity="3", unit_price="333"):
    return client.post("/gifts/apply", data={"employee_no": no, "quantity": quantity, "unit_price": unit_price})


def reqs(client):
    return client.get("/gifts/status.json").get_json()["requests"]


def test_apply_ok_redirects_and_records(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/gifts/")
    assert reqs(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]


def test_tax_rounds_down(admin, emp):
    apply(admin, quantity="1", unit_price="1")  # 1.1 -> 1
    apply(admin, quantity="1", unit_price="15")  # 16.5 -> 16
    apply(admin, quantity="7", unit_price="99999")  # 769992.3 -> 769992
    assert [x["amount_incl_tax"] for x in reqs(admin)] == [1, 16, 769992]


@pytest.mark.parametrize("q,ok", [("0", False), ("1", True), ("30", True), ("31", False), ("-1", False), ("2.5", False), ("abc", False), ("", False)])
def test_quantity_boundaries(admin, emp, q, ok):
    r = apply(admin, quantity=q)
    assert (r.status_code == 302) == ok
    if not ok:
        assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
        assert reqs(admin) == []


@pytest.mark.parametrize("p,ok", [("0", False), ("1", True), ("100000", True), ("100001", False), ("-5", False), ("9.9", False), ("x", False)])
def test_unit_price_boundaries(admin, emp, p, ok):
    r = apply(admin, unit_price=p)
    assert (r.status_code == 302) == ok
    if not ok:
        assert r.status_code == 400 and reqs(admin) == []


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    r = apply(admin)
    assert r.status_code == 400 and reqs(admin) == []


def test_unknown_employee_rejected(admin):
    r = apply(admin, no="123456")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)


def test_approve_by_other_staff(admin, emp, make_employee, client):
    make_employee("200001", "担当", role="staff")
    apply(admin)
    client.post("/logout")
    client.post("/login", data={"employee_no": "200001", "password": "password1"})
    r = client.post("/gifts/approve", data={"request_id": "1"})
    assert r.status_code == 302
    assert reqs(client)[0]["state"] == "approved"


def test_self_approval_blocked_but_reject_allowed(admin, make_employee, client):
    make_employee("200001", "担当", role="staff")
    apply(admin, no="200001")
    client.post("/logout")
    client.post("/login", data={"employee_no": "200001", "password": "password1"})
    r = client.post("/gifts/approve", data={"request_id": "1"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert reqs(client)[0]["state"] == "pending"
    assert client.post("/gifts/reject", data={"request_id": "1"}).status_code == 302
    assert reqs(client)[0]["state"] == "rejected"


def test_only_pending_can_be_decided(admin, emp):
    apply(admin)
    assert admin.post("/gifts/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/gifts/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/gifts/reject", data={"request_id": "1"}).status_code == 400
    apply(admin)
    assert admin.post("/gifts/reject", data={"request_id": "2"}).status_code == 302
    assert admin.post("/gifts/approve", data={"request_id": "2"}).status_code == 400
    assert [x["state"] for x in reqs(admin)] == ["approved", "rejected"]


def test_unknown_request_id(admin, emp):
    assert admin.post("/gifts/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/gifts/reject", data={"request_id": "abc"}).status_code == 400


def test_post_requires_staff(admin, emp, make_employee, client):
    apply(admin)
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert apply(client).status_code == 403
    assert client.post("/gifts/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/gifts/reject", data={"request_id": "1"}).status_code == 403
    assert len(reqs(client)) == 1 and reqs(client)[0]["state"] == "pending"


def test_status_json_visible_to_logged_in_employee(admin, emp, client):
    apply(admin)
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert client.get("/gifts/status.json").status_code == 200


def test_state_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, quantity="2", unit_price="500")
    admin.post("/gifts/approve", data={"request_id": "1"})
    page = admin.get("/gifts/?state=approved").get_data(as_text=True)
    assert 'data-request-id="1"' in page and 'data-request-id="2"' not in page
    detail = admin.get("/gifts/detail?request_id=2").get_data(as_text=True)
    assert "1000" in detail and "1100" in detail and "100001" in detail


def test_audit_log_entries(admin, emp):
    apply(admin)
    apply(admin)
    admin.post("/gifts/approve", data={"request_id": "1"})
    admin.post("/gifts/reject", data={"request_id": "2"})
    apply(admin, quantity="0")  # 失敗は残さない
    rows = admin.get("/audit.json").get_json()["rows"]
    gifts = [(r["action"], r["target"]) for r in rows if r["module"] == "gifts"]
    assert gifts == [("apply", "1"), ("apply", "2"), ("approve", "1"), ("reject", "2")]

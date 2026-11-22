"""ケータリングの申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO, ADMIN_PASSWORD


def apply(client, employee="100001", quantity="3", unit_price="333"):
    return client.post("/catering/apply", data={"employee_no": employee, "quantity": quantity, "unit_price": unit_price})


def rows(client):
    return client.get("/catering/status.json").get_json()["requests"]


def audit_rows(client):
    return [r for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "catering"]


@pytest.fixture
def emp(make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤", role="staff")
    return "100001"


def login_as(client, number, password="password1"):
    client.post("/logout")
    return client.post("/login", data={"employee_no": number, "password": password})


def test_apply_success_and_tax(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/catering/")
    assert rows(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]


@pytest.mark.parametrize("quantity,expected", [("1", True), ("200", True), ("0", False), ("201", False), ("-1", False), ("1.5", False), ("abc", False), ("", False)])
def test_quantity_boundaries(admin, emp, quantity, expected):
    r = apply(admin, quantity=quantity)
    assert (r.status_code == 302) is expected
    if not expected:
        assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
        assert rows(admin) == []


@pytest.mark.parametrize("price,expected", [("1", True), ("100000", True), ("0", False), ("100001", False), ("x", False), ("", False)])
def test_unit_price_boundaries(admin, emp, price, expected):
    r = apply(admin, unit_price=price)
    assert (r.status_code == 302) is expected
    assert len(rows(admin)) == (1 if expected else 0)


def test_tax_rounds_down(admin, emp):
    apply(admin, quantity="1", unit_price="1")  # 1.1 -> 1
    apply(admin, quantity="200", unit_price="100000")  # 22,000,000
    apply(admin, quantity="7", unit_price="13")  # 100.1 -> 100
    assert [r["amount_incl_tax"] for r in rows(admin)] == [1, 22000000, 100]


def test_retired_and_unknown_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert apply(admin, employee="999999").status_code == 400
    assert rows(admin) == []


def test_approve_and_reject_only_pending(admin, emp):
    apply(admin)
    apply(admin)
    assert admin.post("/catering/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/catering/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/catering/reject", data={"request_id": "1"}).status_code == 400
    assert admin.post("/catering/reject", data={"request_id": "2"}).status_code == 302
    assert admin.post("/catering/approve", data={"request_id": "2"}).status_code == 400
    assert [r["state"] for r in rows(admin)] == ["approved", "rejected"]


def test_unknown_request_id(admin, emp):
    assert admin.post("/catering/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/catering/reject", data={"request_id": "abc"}).status_code == 400


def test_applicant_cannot_approve_own_but_can_reject(admin, emp):
    apply(admin, employee=ADMIN_NO)
    apply(admin, employee=ADMIN_NO)
    r = admin.post("/catering/approve", data={"request_id": "1"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"
    assert admin.post("/catering/reject", data={"request_id": "2"}).status_code == 302
    assert rows(admin)[1]["state"] == "rejected"


def test_other_staff_can_approve(admin, emp):
    apply(admin, employee="100002")
    assert admin.post("/catering/approve", data={"request_id": "1"}).status_code == 302


def test_post_requires_staff(admin, emp):
    apply(admin)
    login_as(admin, "100001")
    assert apply(admin).status_code == 403
    assert admin.post("/catering/approve", data={"request_id": "1"}).status_code == 403
    assert admin.post("/catering/reject", data={"request_id": "1"}).status_code == 403
    assert len(rows(admin)) == 1 and rows(admin)[0]["state"] == "pending"


def test_anonymous_is_redirected(client):
    assert client.post("/catering/apply", data={}).status_code == 302
    assert client.get("/catering/status.json").status_code == 302


def test_status_json_visible_to_employee(admin, emp):
    apply(admin)
    login_as(admin, "100001")
    r = admin.get("/catering/status.json")
    assert r.status_code == 200 and len(r.get_json()["requests"]) == 1


def test_list_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, quantity="5", unit_price="100")
    admin.post("/catering/approve", data={"request_id": "2"})
    page = admin.get("/catering/?state=approved").get_data(as_text=True)
    assert 'data-request-id="2"' in page and 'data-request-id="1"' not in page
    detail = admin.get("/catering/detail?request_id=2").get_data(as_text=True)
    assert "550" in detail and "500" in detail and "承認" in detail and "100001" in detail
    assert admin.get("/catering/detail?request_id=99").status_code == 404


def test_audit_recorded_only_on_success(admin, emp):
    apply(admin)
    apply(admin, quantity="0")
    admin.post("/catering/approve", data={"request_id": "1"})
    admin.post("/catering/approve", data={"request_id": "1"})
    apply(admin)
    admin.post("/catering/reject", data={"request_id": "2"})
    assert [(r["action"], r["target"]) for r in audit_rows(admin)] == [("apply", "1"), ("approve", "1"), ("apply", "2"), ("reject", "2")]

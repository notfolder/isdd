"""制服の購入の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO, ADMIN_PASSWORD


def apply(client, number="100001", quantity="3", unit_price="333"):
    return client.post("/uniform_orders/apply", data={"employee_no": number, "quantity": quantity, "unit_price": unit_price})


def requests_of(client):
    return client.get("/uniform_orders/status.json").get_json()["requests"]


def audit_of(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "uniform_orders"]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_apply_success_redirects_and_records(admin, emp):
    response = apply(admin)
    assert response.status_code == 302 and response.headers["Location"].endswith("/uniform_orders/")
    assert requests_of(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]
    assert audit_of(admin) == [("uniform_orders", "apply", "1")]


@pytest.mark.parametrize("quantity", ["1", "20"])
def test_quantity_boundaries_accepted(admin, emp, quantity):
    assert apply(admin, quantity=quantity).status_code == 302


@pytest.mark.parametrize("quantity", ["0", "21", "-1", "1.5", "abc", ""])
def test_quantity_out_of_range_rejected(admin, emp, quantity):
    response = apply(admin, quantity=quantity)
    assert response.status_code == 400
    assert '<p class="error">' in response.get_data(as_text=True)
    assert requests_of(admin) == [] and audit_of(admin) == []


@pytest.mark.parametrize("price", ["1", "100000"])
def test_unit_price_boundaries_accepted(admin, emp, price):
    assert apply(admin, unit_price=price).status_code == 302


@pytest.mark.parametrize("price", ["0", "100001", "-5", "10.5", "x", ""])
def test_unit_price_out_of_range_rejected(admin, emp, price):
    assert apply(admin, unit_price=price).status_code == 400
    assert requests_of(admin) == []


def test_tax_rounds_down(admin, emp):
    apply(admin, quantity="1", unit_price="15")  # 15 + 1 = 16
    apply(admin, quantity="1", unit_price="1")  # 1 + 0 = 1
    apply(admin, quantity="20", unit_price="100000")  # 2,000,000 + 200,000
    assert [r["amount_incl_tax"] for r in requests_of(admin)] == [16, 1, 2200000]


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert requests_of(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, number="999999").status_code == 400
    assert requests_of(admin) == []


def test_approve_pending(admin, emp):
    apply(admin)
    response = admin.post("/uniform_orders/approve", data={"request_id": "1"})
    assert response.status_code == 302
    assert requests_of(admin)[0]["state"] == "approved"
    assert audit_of(admin)[-1] == ("uniform_orders", "approve", "1")


def test_reject_pending(admin, emp):
    apply(admin)
    assert admin.post("/uniform_orders/reject", data={"request_id": "1"}).status_code == 302
    assert requests_of(admin)[0]["state"] == "rejected"
    assert audit_of(admin)[-1] == ("uniform_orders", "reject", "1")


def test_decided_request_cannot_be_decided_again(admin, emp):
    apply(admin)
    admin.post("/uniform_orders/approve", data={"request_id": "1"})
    assert admin.post("/uniform_orders/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/uniform_orders/reject", data={"request_id": "1"}).status_code == 400
    assert requests_of(admin)[0]["state"] == "approved"
    assert len(audit_of(admin)) == 2


def test_cannot_approve_own_request_but_can_reject(admin):
    apply(admin, number=ADMIN_NO)
    apply(admin, number=ADMIN_NO)
    response = admin.post("/uniform_orders/approve", data={"request_id": "1"})
    assert response.status_code == 400 and '<p class="error">' in response.get_data(as_text=True)
    assert requests_of(admin)[0]["state"] == "pending"
    assert admin.post("/uniform_orders/reject", data={"request_id": "2"}).status_code == 302
    assert requests_of(admin)[1]["state"] == "rejected"


def test_unknown_request_id_rejected(admin, emp):
    assert admin.post("/uniform_orders/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/uniform_orders/reject", data={"request_id": "abc"}).status_code == 400


def test_employee_role_cannot_post(admin, make_employee, client, app):
    make_employee("100002", "佐藤")
    other = app.test_client()
    other.post("/login", data={"employee_no": "100002", "password": "password1"})
    assert apply(other, number="100002").status_code == 403
    apply(admin, number="100002")
    assert other.post("/uniform_orders/approve", data={"request_id": "1"}).status_code == 403
    assert other.get("/uniform_orders/status.json").status_code == 200
    assert requests_of(admin)[0]["state"] == "pending"


def test_login_required(client):
    assert client.get("/uniform_orders/status.json").status_code == 302
    assert client.post("/uniform_orders/apply", data={}).status_code == 302


def test_list_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, quantity="2", unit_price="100")
    admin.post("/uniform_orders/reject", data={"request_id": "2"})
    html = admin.get("/uniform_orders/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    detail = admin.get("/uniform_orders/detail?request_id=1").get_data(as_text=True)
    assert "999" in detail and "1098" in detail and "山田" in detail

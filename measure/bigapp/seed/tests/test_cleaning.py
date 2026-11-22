"""クリーニングの申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO, ADMIN_PASSWORD, get_db


@pytest.fixture
def worker(make_employee):
    return make_employee("100001", "山田")


def apply(client, employee="100001", quantity="3", unit_price="333"):
    return client.post("/cleaning/apply", data={"employee_no": employee, "quantity": quantity, "unit_price": unit_price})


def requests_json(client):
    return client.get("/cleaning/status.json").get_json()["requests"]


def login(client, number, password):
    client.post("/logout")
    client.post("/login", data={"employee_no": number, "password": password})


def audit_rows(app):
    with app.app_context():
        return [tuple(r) for r in get_db().execute("SELECT module, action, target FROM audit_log WHERE module = 'cleaning' ORDER BY id")]


def test_apply_success_redirects_and_records(admin, worker, app):
    response = apply(admin)
    assert response.status_code == 302 and response.headers["Location"].endswith("/cleaning/")
    assert requests_json(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]
    assert audit_rows(app) == [("cleaning", "apply", "1")]


@pytest.mark.parametrize("quantity,ok", [("0", False), ("1", True), ("20", True), ("21", False), ("-1", False), ("1.5", False), ("", False), ("abc", False)])
def test_quantity_boundaries(admin, worker, quantity, ok):
    response = apply(admin, quantity=quantity)
    assert response.status_code == (302 if ok else 400)
    if not ok:
        assert '<p class="error">' in response.get_data(as_text=True)
        assert requests_json(admin) == []


@pytest.mark.parametrize("price,ok", [("0", False), ("1", True), ("100000", True), ("100001", False), ("x", False), ("", False)])
def test_unit_price_boundaries(admin, worker, price, ok):
    assert apply(admin, unit_price=price).status_code == (302 if ok else 400)


@pytest.mark.parametrize("quantity,price,expected", [(1, 1, 1), (1, 9, 9), (3, 333, 1098), (1, 15, 16), (7, 13, 100), (20, 100000, 2200000)])
def test_tax_is_rounded_down(admin, worker, quantity, price, expected):
    apply(admin, quantity=str(quantity), unit_price=str(price))
    assert requests_json(admin)[0]["amount_incl_tax"] == expected


def test_retired_employee_rejected(admin, worker, app):
    admin.post("/employees/retire", data={"employee_no": worker})
    response = apply(admin)
    assert response.status_code == 400 and '<p class="error">' in response.get_data(as_text=True)
    assert requests_json(admin) == [] and audit_rows(app) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, employee="123456").status_code == 400


def test_approve_and_audit(admin, worker, app):
    apply(admin)
    response = admin.post("/cleaning/approve", data={"request_id": "1"})
    assert response.status_code == 302
    assert requests_json(admin)[0]["state"] == "approved"
    assert audit_rows(app)[-1] == ("cleaning", "approve", "1")


def test_reject_and_audit(admin, worker, app):
    apply(admin)
    assert admin.post("/cleaning/reject", data={"request_id": "1"}).status_code == 302
    assert requests_json(admin)[0]["state"] == "rejected"
    assert audit_rows(app)[-1] == ("cleaning", "reject", "1")


def test_only_pending_can_be_decided(admin, worker, app):
    apply(admin)
    admin.post("/cleaning/approve", data={"request_id": "1"})
    count = len(audit_rows(app))
    assert admin.post("/cleaning/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/cleaning/reject", data={"request_id": "1"}).status_code == 400
    assert requests_json(admin)[0]["state"] == "approved"
    assert len(audit_rows(app)) == count


def test_unknown_request_id(admin):
    assert admin.post("/cleaning/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/cleaning/reject", data={"request_id": "abc"}).status_code == 400


def test_self_approval_blocked_but_rejection_allowed(admin, app):
    apply(admin, employee=ADMIN_NO)
    apply(admin, employee=ADMIN_NO)
    response = admin.post("/cleaning/approve", data={"request_id": "1"})
    assert response.status_code == 400 and '<p class="error">' in response.get_data(as_text=True)
    assert requests_json(admin)[0]["state"] == "pending"
    assert admin.post("/cleaning/reject", data={"request_id": "2"}).status_code == 302
    assert requests_json(admin)[1]["state"] == "rejected"


def test_other_staff_can_approve(admin, make_employee):
    make_employee("200001", "佐藤", role="staff")
    apply(admin, employee=ADMIN_NO)
    login(admin, "200001", "password1")
    assert admin.post("/cleaning/approve", data={"request_id": "1"}).status_code == 302
    assert requests_json(admin)[0]["state"] == "approved"


def test_non_staff_cannot_change_but_can_read(admin, worker, make_employee):
    apply(admin)
    login(admin, "100001", "password1")
    assert apply(admin).status_code == 403
    assert admin.post("/cleaning/approve", data={"request_id": "1"}).status_code == 403
    assert admin.post("/cleaning/reject", data={"request_id": "1"}).status_code == 403
    assert admin.get("/cleaning/").status_code == 200
    assert len(requests_json(admin)) == 1


def test_login_required(client):
    assert client.get("/cleaning/").status_code == 302
    assert client.post("/cleaning/apply", data={}).status_code == 302


def test_state_filter(admin, worker):
    apply(admin)
    apply(admin)
    admin.post("/cleaning/reject", data={"request_id": "2"})
    page = admin.get("/cleaning/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in page and 'data-request-id="1"' not in page
    assert admin.get("/cleaning/?state=bogus").status_code == 400


def test_detail_page(admin, worker):
    apply(admin)
    page = admin.get("/cleaning/detail?request_id=1").get_data(as_text=True)
    for text in ("333", "999", "1098", "山田", "申請中"):
        assert text in page
    assert admin.get("/cleaning/detail?request_id=9").status_code == 404

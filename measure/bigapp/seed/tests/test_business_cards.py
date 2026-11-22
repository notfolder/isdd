"""名刺の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO
from app.modules.business_cards.logic import tax_included


def apply(client, no="100001", quantity="3", unit_price="333"):
    return client.post("/business_cards/apply", data={"employee_no": no, "quantity": quantity, "unit_price": unit_price})


def requests_json(client):
    return client.get("/business_cards/status.json").get_json()["requests"]


def audit_rows(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "business_cards"]


def test_tax_included_rounds_down():
    assert tax_included(3, 333) == 1098  # 999 * 1.1 = 1098.9
    assert tax_included(1, 1) == 1  # 1.1 -> 1
    assert tax_included(1, 9) == 9  # 9.9 -> 9
    assert tax_included(500, 100000) == 55000000


def test_apply_creates_pending_request_and_redirects(admin, make_employee):
    make_employee("100001")
    response = apply(admin)
    assert response.status_code == 302 and response.headers["Location"].endswith("/business_cards/")
    assert requests_json(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]


@pytest.mark.parametrize("quantity,ok", [("0", False), ("1", True), ("500", True), ("501", False), ("-1", False), ("1.5", False), ("", False), ("abc", False)])
def test_quantity_boundaries(admin, make_employee, quantity, ok):
    make_employee("100001")
    response = apply(admin, quantity=quantity)
    assert response.status_code == (302 if ok else 400)
    assert len(requests_json(admin)) == (1 if ok else 0)


@pytest.mark.parametrize("price,ok", [("0", False), ("1", True), ("100000", True), ("100001", False), ("-5", False), ("1e3", False), ("", False)])
def test_unit_price_boundaries(admin, make_employee, price, ok):
    make_employee("100001")
    response = apply(admin, unit_price=price)
    assert response.status_code == (302 if ok else 400)
    assert len(requests_json(admin)) == (1 if ok else 0)


def test_invalid_input_shows_error_and_does_not_change_data(admin, make_employee):
    make_employee("100001")
    response = apply(admin, quantity="0")
    assert response.status_code == 400
    assert '<p class="error">' in response.get_data(as_text=True)
    assert audit_rows(admin) == []


def test_retired_and_unknown_employee_rejected(admin, make_employee):
    make_employee("100001")
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin, "100001").status_code == 400
    assert apply(admin, "999999").status_code == 400
    assert requests_json(admin) == []
    assert audit_rows(admin) == []


def test_approve_and_reject_pending(admin, make_employee):
    make_employee("100001")
    apply(admin)
    apply(admin)
    assert admin.post("/business_cards/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/business_cards/reject", data={"request_id": "2"}).status_code == 302
    assert [r["state"] for r in requests_json(admin)] == ["approved", "rejected"]


def test_only_pending_can_be_decided(admin, make_employee):
    make_employee("100001")
    apply(admin)
    admin.post("/business_cards/approve", data={"request_id": "1"})
    assert admin.post("/business_cards/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/business_cards/reject", data={"request_id": "1"}).status_code == 400
    apply(admin)
    admin.post("/business_cards/reject", data={"request_id": "2"})
    assert admin.post("/business_cards/approve", data={"request_id": "2"}).status_code == 400
    assert [r["state"] for r in requests_json(admin)] == ["approved", "rejected"]


def test_unknown_request_id_is_400(admin):
    assert admin.post("/business_cards/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/business_cards/reject", data={"request_id": "abc"}).status_code == 400


def test_applicant_cannot_approve_own_request_but_can_reject(app, admin, make_employee):
    client = app.test_client()
    make_employee("200001", "担当 二", role="staff")
    apply(admin, "200001")
    apply(admin, "200001")
    client.post("/login", data={"employee_no": "200001", "password": "password1"})
    response = client.post("/business_cards/approve", data={"request_id": "1"})
    assert response.status_code == 400 and '<p class="error">' in response.get_data(as_text=True)
    assert requests_json(client)[0]["state"] == "pending"
    assert client.post("/business_cards/reject", data={"request_id": "2"}).status_code == 302
    assert requests_json(client)[1]["state"] == "rejected"
    # 別の担当者（管理者）なら承認できる
    assert admin.post("/business_cards/approve", data={"request_id": "1"}).status_code == 302


def test_post_requires_staff(app, admin, make_employee):
    make_employee("100001")
    client = app.test_client()
    assert client.post("/business_cards/apply", data={}).status_code == 302  # 未ログインはログインへ
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    for path in ("apply", "approve", "reject"):
        assert client.post(f"/business_cards/{path}", data={"employee_no": "100001", "quantity": "1", "unit_price": "1", "request_id": "1"}).status_code == 403
    assert requests_json(admin) == []


def test_audit_records_each_operation(admin, make_employee):
    make_employee("100001")
    apply(admin)
    apply(admin)
    admin.post("/business_cards/approve", data={"request_id": "1"})
    admin.post("/business_cards/reject", data={"request_id": "2"})
    assert audit_rows(admin) == [
        ("business_cards", "apply", "1"),
        ("business_cards", "apply", "2"),
        ("business_cards", "approve", "1"),
        ("business_cards", "reject", "2"),
    ]


def test_index_filters_by_state(admin, make_employee):
    make_employee("100001")
    apply(admin, quantity="7")
    apply(admin, quantity="9")
    admin.post("/business_cards/reject", data={"request_id": "2"})
    page = admin.get("/business_cards/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in page and 'data-request-id="1"' not in page
    assert 'data-request-id="1"' in admin.get("/business_cards/?state=pending").get_data(as_text=True)


def test_detail_page(admin, make_employee):
    make_employee("100001", "山田 太郎")
    apply(admin, quantity="3", unit_price="333")
    page = admin.get("/business_cards/detail?request_id=1").get_data(as_text=True)
    for text in ("100001", "山田 太郎", "999", "1098", "申請中"):
        assert text in page
    assert admin.get("/business_cards/detail?request_id=9").status_code == 404


def test_status_json_open_to_employees_but_not_anonymous(app, admin, make_employee):
    make_employee("100001")
    apply(admin)
    other = app.test_client()
    assert other.get("/business_cards/status.json").status_code == 302
    other.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert other.get("/business_cards/status.json").get_json()["requests"][0]["id"] == 1

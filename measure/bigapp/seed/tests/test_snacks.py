"""茶菓の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO


def apply(client, employee="100001", quantity="3", unit_price="333"):
    return client.post("/snacks/apply", data={"employee_no": employee, "quantity": quantity, "unit_price": unit_price})


def rows(client):
    return client.get("/snacks/status.json").get_json()["requests"]


def audit_rows(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "snacks"]


def test_apply_calculates_tax_included_amount(admin, make_employee):
    make_employee("100001")
    response = apply(admin)
    assert response.status_code == 302 and response.headers["Location"].endswith("/snacks/")
    assert rows(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]


@pytest.mark.parametrize("quantity,price,expected", [(1, 1, 1), (1, 10, 11), (3, 333, 1098), (100, 100000, 11000000), (1, 99999, 109998)])
def test_amount_is_rounded_down(admin, make_employee, quantity, price, expected):
    make_employee("100001")
    apply(admin, quantity=str(quantity), unit_price=str(price))
    assert rows(admin)[0]["amount_incl_tax"] == expected


@pytest.mark.parametrize("quantity", ["1", "100"])
def test_quantity_boundaries_accepted(admin, make_employee, quantity):
    make_employee("100001")
    assert apply(admin, quantity=quantity).status_code == 302


@pytest.mark.parametrize("quantity", ["0", "101", "-1", "abc", "", "1.5"])
def test_quantity_out_of_range_rejected(admin, make_employee, quantity):
    make_employee("100001")
    response = apply(admin, quantity=quantity)
    assert response.status_code == 400 and 'class="error"' in response.get_data(as_text=True)
    assert rows(admin) == []


@pytest.mark.parametrize("price,status", [("1", 302), ("100000", 302), ("0", 400), ("100001", 400), ("x", 400)])
def test_unit_price_boundaries(admin, make_employee, price, status):
    make_employee("100001")
    assert apply(admin, unit_price=price).status_code == status


def test_retired_and_unknown_employee_rejected(admin, make_employee):
    make_employee("100001")
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert apply(admin, employee="999999").status_code == 400
    assert rows(admin) == []


def test_approve_and_reject(admin, make_employee):
    make_employee("100001")
    apply(admin)
    apply(admin)
    assert admin.post("/snacks/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/snacks/reject", data={"request_id": "2"}).status_code == 302
    assert [r["state"] for r in rows(admin)] == ["approved", "rejected"]


def test_decided_request_cannot_be_decided_again(admin, make_employee):
    make_employee("100001")
    apply(admin)
    admin.post("/snacks/approve", data={"request_id": "1"})
    assert admin.post("/snacks/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/snacks/reject", data={"request_id": "1"}).status_code == 400
    assert rows(admin)[0]["state"] == "approved"


def test_unknown_request_is_400(admin):
    assert admin.post("/snacks/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/snacks/reject", data={"request_id": "abc"}).status_code == 400


def test_cannot_approve_own_request_but_can_reject(admin):
    apply(admin, employee=ADMIN_NO)
    apply(admin, employee=ADMIN_NO)
    response = admin.post("/snacks/approve", data={"request_id": "1"})
    assert response.status_code == 400 and 'class="error"' in response.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"
    assert admin.post("/snacks/reject", data={"request_id": "2"}).status_code == 302
    assert rows(admin)[1]["state"] == "rejected"


def test_state_filter_on_list(admin, make_employee):
    make_employee("100001")
    apply(admin)
    apply(admin, quantity="7")
    admin.post("/snacks/reject", data={"request_id": "2"})
    body = admin.get("/snacks/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in body and 'data-request-id="1"' not in body


def test_detail_page(admin, make_employee):
    make_employee("100001", "山田 太郎")
    apply(admin)
    body = admin.get("/snacks/detail?request_id=1").get_data(as_text=True)
    for text in ("100001", "山田 太郎", "333", "1098", "申請中"):
        assert text in body
    assert admin.get("/snacks/detail?request_id=9").status_code == 400


def test_audit_log_written_only_on_success(admin, make_employee):
    make_employee("100001")
    apply(admin)
    apply(admin, quantity="0")
    admin.post("/snacks/approve", data={"request_id": "1"})
    admin.post("/snacks/reject", data={"request_id": "1"})
    assert audit_rows(admin) == [("snacks", "apply", "1"), ("snacks", "approve", "1")]


def test_post_requires_staff(client, admin, make_employee):
    make_employee("100001")
    make_employee("100002")
    apply(admin)
    client.post("/logout")
    assert apply(client).status_code == 302  # 未ログインはログイン画面へ
    client.post("/login", data={"employee_no": "100002", "password": "password1"})
    assert apply(client).status_code == 403
    assert client.post("/snacks/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/snacks/reject", data={"request_id": "1"}).status_code == 403
    assert client.get("/snacks/status.json").status_code == 200
    assert len(client.get("/snacks/status.json").get_json()["requests"]) == 1


def test_status_json_requires_login(client):
    assert client.get("/snacks/status.json").status_code == 302

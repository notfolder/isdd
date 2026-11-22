"""翻訳の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO


def apply(client, employee_no, quantity, unit_price):
    return client.post("/translations/apply", data={"employee_no": employee_no, "quantity": quantity, "unit_price": unit_price})


def items(client):
    return client.get("/translations/status.json").get_json()["requests"]


def audit_rows(client):
    return [r for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "translations"]


def test_apply_success_redirects_and_records(admin, make_employee):
    make_employee("100001")
    r = apply(admin, "100001", 3, 333)
    assert r.status_code == 302 and r.headers["Location"].endswith("/translations/")
    assert items(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]
    assert [(a["action"], a["target"]) for a in audit_rows(admin)] == [("apply", "1")]


@pytest.mark.parametrize("qty", [1, 50])
def test_quantity_boundaries_accepted(admin, make_employee, qty):
    make_employee("100001")
    assert apply(admin, "100001", qty, 100).status_code == 302


@pytest.mark.parametrize("qty", ["0", "51", "-1", "abc", "", "1.5"])
def test_quantity_invalid_rejected(admin, make_employee, qty):
    make_employee("100001")
    r = apply(admin, "100001", qty, 100)
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert items(admin) == [] and audit_rows(admin) == []


@pytest.mark.parametrize("price", [1, 100000])
def test_unit_price_boundaries_accepted(admin, make_employee, price):
    make_employee("100001")
    assert apply(admin, "100001", 1, price).status_code == 302


@pytest.mark.parametrize("price", ["0", "100001", "-5", "x", ""])
def test_unit_price_invalid_rejected(admin, make_employee, price):
    make_employee("100001")
    assert apply(admin, "100001", 1, price).status_code == 400
    assert items(admin) == []


@pytest.mark.parametrize("qty,price,expected", [(1, 1, 1), (1, 9, 9), (1, 10, 11), (3, 333, 1098), (7, 19, 146), (50, 100000, 5500000)])
def test_tax_rounds_down(admin, make_employee, qty, price, expected):
    make_employee("100001")
    apply(admin, "100001", qty, price)
    assert items(admin)[0]["amount_incl_tax"] == expected


def test_detail_page_shows_amounts(admin, make_employee):
    make_employee("100001", "山田")
    apply(admin, "100001", 3, 333)
    html = admin.get("/translations/detail?request_id=1").get_data(as_text=True)
    assert "999" in html and "1098" in html and "100001" in html
    assert admin.get("/translations/detail?request_id=99").status_code == 404


def test_retired_employee_rejected(admin, make_employee):
    make_employee("100001")
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin, "100001", 1, 100).status_code == 400
    assert items(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, "999999", 1, 100).status_code == 400


def test_approve_by_other_staff(admin, make_employee, client):
    make_employee("100001")
    apply(admin, "100001", 1, 100)
    r = admin.post("/translations/approve", data={"request_id": 1})
    assert r.status_code == 302
    assert items(admin)[0]["state"] == "approved"
    assert ("approve", "1") in [(a["action"], a["target"]) for a in audit_rows(admin)]


def test_self_approval_rejected_but_reject_allowed(admin):
    apply(admin, ADMIN_NO, 1, 100)
    r = admin.post("/translations/approve", data={"request_id": 1})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert items(admin)[0]["state"] == "pending"
    assert admin.post("/translations/reject", data={"request_id": 1}).status_code == 302
    assert items(admin)[0]["state"] == "rejected"
    assert ("reject", "1") in [(a["action"], a["target"]) for a in audit_rows(admin)]


def test_only_pending_can_be_decided(admin, make_employee):
    make_employee("100001")
    apply(admin, "100001", 1, 100)
    admin.post("/translations/approve", data={"request_id": 1})
    assert admin.post("/translations/reject", data={"request_id": 1}).status_code == 400
    assert admin.post("/translations/approve", data={"request_id": 1}).status_code == 400
    apply(admin, "100001", 1, 100)
    admin.post("/translations/reject", data={"request_id": 2})
    assert admin.post("/translations/approve", data={"request_id": 2}).status_code == 400
    assert [i["state"] for i in items(admin)] == ["approved", "rejected"]


def test_unknown_request_id_rejected(admin):
    assert admin.post("/translations/approve", data={"request_id": 99}).status_code == 400
    assert admin.post("/translations/reject", data={"request_id": "abc"}).status_code == 400


def test_state_filter(admin, make_employee):
    make_employee("100001")
    apply(admin, "100001", 1, 100)
    apply(admin, "100001", 2, 200)
    admin.post("/translations/reject", data={"request_id": 2})
    html = admin.get("/translations/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html


def test_non_staff_cannot_post(admin, make_employee, client):
    make_employee("100001")
    apply(admin, "100001", 1, 100)
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert apply(client, "100001", 1, 100).status_code == 403
    assert client.post("/translations/approve", data={"request_id": 1}).status_code == 403
    assert client.post("/translations/reject", data={"request_id": 1}).status_code == 403
    assert client.get("/translations/status.json").status_code == 200
    assert len(items(client)) == 1


def test_login_required(app):
    c = app.test_client()
    assert c.get("/translations/status.json").status_code == 302
    assert c.get("/translations/").status_code == 302

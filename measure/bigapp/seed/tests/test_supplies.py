"""消耗品の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO, get_db


def apply(client, employee_no="100001", quantity="3", unit_price="333"):
    return client.post("/supplies/apply", data={"employee_no": employee_no, "quantity": quantity, "unit_price": unit_price})


def rows(client):
    return client.get("/supplies/status.json").get_json()["requests"]


def audit_rows(app):
    with app.app_context():
        return [dict(r) for r in get_db().execute("SELECT * FROM audit_log WHERE module = 'supplies' ORDER BY id")]


def test_apply_success_redirects_and_records(app, admin, make_employee):
    make_employee("100001")
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/supplies/")
    assert rows(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]
    log = audit_rows(app)
    assert [(l["action"], l["target"]) for l in log] == [("apply", "1")]


@pytest.mark.parametrize("quantity,unit_price,expected", [(1, 1, 1), (1, 9, 9), (3, 333, 1098), (7, 15, 115), (100, 100000, 11000000)])
def test_tax_included_amount_is_floored(admin, make_employee, quantity, unit_price, expected):
    make_employee("100001")
    assert apply(admin, quantity=str(quantity), unit_price=str(unit_price)).status_code == 302
    assert rows(admin)[0]["amount_incl_tax"] == expected


@pytest.mark.parametrize("quantity", ["0", "101", "-1", "1.5", "abc", ""])
def test_quantity_out_of_range_is_rejected(app, admin, make_employee, quantity):
    make_employee("100001")
    r = apply(admin, quantity=quantity)
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert rows(admin) == []
    assert audit_rows(app) == []


@pytest.mark.parametrize("quantity", ["1", "100"])
def test_quantity_boundaries_accepted(admin, make_employee, quantity):
    make_employee("100001")
    assert apply(admin, quantity=quantity).status_code == 302


@pytest.mark.parametrize("unit_price", ["0", "100001", "-5", "9.9", "x", ""])
def test_unit_price_out_of_range_is_rejected(admin, make_employee, unit_price):
    make_employee("100001")
    assert apply(admin, unit_price=unit_price).status_code == 400
    assert rows(admin) == []


@pytest.mark.parametrize("unit_price", ["1", "100000"])
def test_unit_price_boundaries_accepted(admin, make_employee, unit_price):
    make_employee("100001")
    assert apply(admin, unit_price=unit_price).status_code == 302


def test_unknown_employee_is_rejected(admin):
    r = apply(admin, employee_no="999999")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert rows(admin) == []


def test_retired_employee_is_rejected(admin, make_employee):
    make_employee("100001")
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert rows(admin) == []


def test_approve_by_another_staff(app, admin, make_employee):
    make_employee("100001")
    apply(admin)
    r = admin.post("/supplies/approve", data={"request_id": "1"})
    # 管理者 (900001) は申請者 (100001) ではないので承認できる
    assert r.status_code == 302
    assert rows(admin)[0]["state"] == "approved"
    assert ("approve", "1") in [(l["action"], l["target"]) for l in audit_rows(app)]


def test_staff_cannot_approve_own_request(app, admin):
    apply(admin, employee_no=ADMIN_NO)
    r = admin.post("/supplies/approve", data={"request_id": "1"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"
    assert all(l["action"] != "approve" for l in audit_rows(app))


def test_staff_can_reject_own_request(app, admin):
    apply(admin, employee_no=ADMIN_NO)
    assert admin.post("/supplies/reject", data={"request_id": "1"}).status_code == 302
    assert rows(admin)[0]["state"] == "rejected"
    assert ("reject", "1") in [(l["action"], l["target"]) for l in audit_rows(app)]


def test_only_pending_can_be_approved_or_rejected(admin, make_employee):
    make_employee("100001")
    apply(admin)
    apply(admin)
    admin.post("/supplies/approve", data={"request_id": "1"})
    admin.post("/supplies/reject", data={"request_id": "2"})
    for path in ("/supplies/approve", "/supplies/reject"):
        for request_id in ("1", "2"):
            assert admin.post(path, data={"request_id": request_id}).status_code == 400
    assert [r["state"] for r in rows(admin)] == ["approved", "rejected"]


def test_unknown_request_id_is_rejected(admin):
    assert admin.post("/supplies/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/supplies/reject", data={"request_id": "abc"}).status_code == 400


def test_post_requires_staff(client, admin, make_employee):
    make_employee("100001")
    apply(admin)
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert apply(client).status_code == 403
    assert client.post("/supplies/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/supplies/reject", data={"request_id": "1"}).status_code == 403
    assert rows(client)[0]["state"] == "pending"  # 社員でも status.json は見られる


def test_status_json_requires_login(client):
    assert client.get("/supplies/status.json").status_code == 302


def test_list_filter_and_detail(admin, make_employee):
    make_employee("100001", name="山田")
    apply(admin)
    apply(admin, quantity="5", unit_price="100")
    admin.post("/supplies/reject", data={"request_id": "2"})
    html = admin.get("/supplies/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    detail = admin.get("/supplies/detail?request_id=1").get_data(as_text=True)
    assert "山田" in detail and "1098" in detail and "999" in detail
    assert admin.get("/supplies/detail?request_id=77").status_code == 400

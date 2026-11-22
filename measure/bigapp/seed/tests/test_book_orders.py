"""書籍の購入の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO
from app.modules.book_orders.rules import gross_amount


def apply(client, no="100001", q="3", p="333"):
    return client.post("/book_orders/apply", data={"employee_no": no, "quantity": q, "unit_price": p})


def rows(client):
    return client.get("/book_orders/status.json").get_json()["requests"]


def audit_rows(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "book_orders"]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_apply_success_redirects_and_records(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/book_orders/")
    assert rows(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]
    assert audit_rows(admin) == [("book_orders", "apply", "1")]


def test_gross_amount_rounds_down():
    assert gross_amount(3, 333) == 1098  # 999 * 1.1 = 1098.9
    assert gross_amount(1, 1) == 1  # 1.1
    assert gross_amount(1, 9) == 9  # 9.9
    assert gross_amount(20, 100000) == 2200000


def test_gross_amount_saved(admin, emp):
    apply(admin, q="1", p="19")  # 20.9
    assert rows(admin)[0]["amount_incl_tax"] == 20


@pytest.mark.parametrize("q", ["1", "20"])
def test_quantity_boundaries_ok(admin, emp, q):
    assert apply(admin, q=q).status_code == 302


@pytest.mark.parametrize("q", ["0", "21", "-1", "abc", "", "1.5"])
def test_quantity_out_of_range(admin, emp, q):
    r = apply(admin, q=q)
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin) == []
    assert audit_rows(admin) == []


@pytest.mark.parametrize("p", ["1", "100000"])
def test_unit_price_boundaries_ok(admin, emp, p):
    assert apply(admin, p=p).status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "-5", "x", "", "10.5"])
def test_unit_price_out_of_range(admin, emp, p):
    assert apply(admin, p=p).status_code == 400
    assert rows(admin) == []


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    r = apply(admin)
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, no="999999").status_code == 400


def test_approve_other_person(admin, emp):
    apply(admin)
    r = admin.post("/book_orders/approve", data={"request_id": "1"})
    assert r.status_code == 302
    assert rows(admin)[0]["state"] == "approved"
    assert ("book_orders", "approve", "1") in audit_rows(admin)


def test_cannot_approve_own_request(admin):
    apply(admin, no=ADMIN_NO)
    r = admin.post("/book_orders/approve", data={"request_id": "1"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"


def test_can_reject_own_request(admin):
    apply(admin, no=ADMIN_NO)
    assert admin.post("/book_orders/reject", data={"request_id": "1"}).status_code == 302
    assert rows(admin)[0]["state"] == "rejected"
    assert ("book_orders", "reject", "1") in audit_rows(admin)


def test_decided_request_cannot_change(admin, emp):
    apply(admin)
    admin.post("/book_orders/approve", data={"request_id": "1"})
    assert admin.post("/book_orders/reject", data={"request_id": "1"}).status_code == 400
    assert admin.post("/book_orders/approve", data={"request_id": "1"}).status_code == 400
    assert rows(admin)[0]["state"] == "approved"
    apply(admin)
    admin.post("/book_orders/reject", data={"request_id": "2"})
    assert admin.post("/book_orders/approve", data={"request_id": "2"}).status_code == 400
    assert rows(admin)[1]["state"] == "rejected"


def test_unknown_request_id(admin):
    assert admin.post("/book_orders/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/book_orders/reject", data={"request_id": "abc"}).status_code == 400


def test_post_requires_staff(client, admin, emp):
    admin.post("/employees/new", data={"employee_no": "100002", "name": "社員", "role": "employee"})
    apply(admin)
    client.post("/logout")
    client.post("/login", data={"employee_no": "100002", "password": "password1"})
    assert apply(client).status_code == 403
    assert client.post("/book_orders/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/book_orders/reject", data={"request_id": "1"}).status_code == 403
    assert client.get("/book_orders/status.json").status_code == 200  # 社員も見られる
    assert rows(client)[0]["state"] == "pending"


def test_anonymous_cannot_post(client):
    assert client.post("/book_orders/apply", data={}).status_code == 302


def test_list_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, q="2", p="100")
    admin.post("/book_orders/approve", data={"request_id": "1"})
    html = admin.get("/book_orders/?state=pending").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    d = admin.get("/book_orders/detail?request_id=2").get_data(as_text=True)
    assert "220" in d and "200" in d and "申請中" in d and "100001" in d
    assert admin.get("/book_orders/detail?request_id=9").status_code == 404

"""文具の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO, ADMIN_PASSWORD
from app.modules.stationery import rules


def apply(client, no="100001", quantity="3", unit_price="333"):
    return client.post("/stationery/apply", data={"employee_no": no, "quantity": quantity, "unit_price": unit_price})


def requests_of(client):
    return client.get("/stationery/status.json").get_json()["requests"]


def login(client, no, password="password1"):
    client.post("/logout")
    return client.post("/login", data={"employee_no": no, "password": password})


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_apply_success_redirects(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/stationery/")
    assert requests_of(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]


def test_tax_rounds_down(admin, emp):
    apply(admin, quantity="1", unit_price="15")  # 15 + 1 = 16（1.5 は切り捨て）
    apply(admin, quantity="1", unit_price="9")  # 9 + 0 = 9
    assert [r["amount_incl_tax"] for r in requests_of(admin)] == [16, 9]
    assert rules.total(3, 333) == 1098


@pytest.mark.parametrize("q", ["1", "100"])
def test_quantity_boundaries_ok(admin, emp, q):
    assert apply(admin, quantity=q).status_code == 302


@pytest.mark.parametrize("q", ["0", "101", "-1", "1.5", "abc", ""])
def test_quantity_boundaries_rejected(admin, emp, q):
    r = apply(admin, quantity=q)
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert requests_of(admin) == []


@pytest.mark.parametrize("p", ["1", "100000"])
def test_unit_price_boundaries_ok(admin, emp, p):
    assert apply(admin, unit_price=p).status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "-5", "1e3", ""])
def test_unit_price_boundaries_rejected(admin, emp, p):
    assert apply(admin, unit_price=p).status_code == 400
    assert requests_of(admin) == []


def test_max_amount(admin, emp):
    apply(admin, quantity="100", unit_price="100000")
    assert requests_of(admin)[0]["amount_incl_tax"] == 11000000


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert requests_of(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, no="999999").status_code == 400


def test_non_staff_cannot_post(admin, emp):
    apply(admin)
    login(admin, "100001")
    assert apply(admin).status_code == 403
    assert admin.post("/stationery/approve", data={"request_id": "1"}).status_code == 403
    assert admin.post("/stationery/reject", data={"request_id": "1"}).status_code == 403
    assert len(requests_of(admin)) == 1 and requests_of(admin)[0]["state"] == "pending"


def test_approve_other_person(admin, emp):
    apply(admin)
    r = admin.post("/stationery/approve", data={"request_id": "1"})
    assert r.status_code == 302
    assert requests_of(admin)[0]["state"] == "approved"


def test_cannot_approve_own_request(admin):
    apply(admin, no=ADMIN_NO)
    r = admin.post("/stationery/approve", data={"request_id": "1"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert requests_of(admin)[0]["state"] == "pending"


def test_can_reject_own_request(admin):
    apply(admin, no=ADMIN_NO)
    assert admin.post("/stationery/reject", data={"request_id": "1"}).status_code == 302
    assert requests_of(admin)[0]["state"] == "rejected"


def test_decided_request_cannot_change_again(admin, emp):
    apply(admin)
    admin.post("/stationery/approve", data={"request_id": "1"})
    assert admin.post("/stationery/reject", data={"request_id": "1"}).status_code == 400
    assert admin.post("/stationery/approve", data={"request_id": "1"}).status_code == 400
    assert requests_of(admin)[0]["state"] == "approved"
    apply(admin)
    admin.post("/stationery/reject", data={"request_id": "2"})
    assert admin.post("/stationery/approve", data={"request_id": "2"}).status_code == 400
    assert requests_of(admin)[1]["state"] == "rejected"


def test_unknown_request_id_rejected(admin):
    assert admin.post("/stationery/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/stationery/reject", data={"request_id": "x"}).status_code == 400


def test_audit_records(admin, emp):
    apply(admin)
    apply(admin)
    admin.post("/stationery/approve", data={"request_id": "1"})
    admin.post("/stationery/reject", data={"request_id": "2"})
    apply(admin, quantity="0")  # 失敗は残さない
    rows = [(r["module"], r["action"], r["target"]) for r in admin.get("/audit.json").get_json()["rows"] if r["module"] == "stationery"]
    assert rows == [("stationery", "apply", "1"), ("stationery", "apply", "2"), ("stationery", "approve", "1"), ("stationery", "reject", "2")]


def test_index_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, quantity="2", unit_price="100")
    admin.post("/stationery/approve", data={"request_id": "1"})
    page = admin.get("/stationery/?state=approved").get_data(as_text=True)
    assert 'data-request-id="1"' in page and 'data-request-id="2"' not in page
    detail = admin.get("/stationery/detail?request_id=2").get_data(as_text=True)
    assert "220" in detail and "200" in detail and "pending" in detail and "100001" in detail
    assert admin.get("/stationery/detail?request_id=9").status_code == 404


def test_status_json_visible_to_employee_and_login_required(client, admin, emp):
    apply(admin)
    login(admin, "100001")
    assert admin.get("/stationery/status.json").status_code == 200
    client.post("/logout")
    assert client.get("/stationery/status.json").status_code == 302

"""宅配便の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO, ADMIN_PASSWORD


def apply(client, no="100001", q="3", p="333"):
    return client.post("/courier/apply", data={"employee_no": no, "quantity": q, "unit_price": p})


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def rows(client):
    return client.get("/courier/status.json").get_json()["requests"]


def test_apply_success_and_amount(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/courier/")
    assert rows(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]


def test_tax_rounds_down(admin, emp):
    apply(admin, q="1", p="1")  # 1.1 円 -> 1
    apply(admin, q="1", p="19")  # 20.9 -> 20
    assert [x["amount_incl_tax"] for x in rows(admin)] == [1, 20]


@pytest.mark.parametrize("q", ["0", "31", "-1", "1.5", "abc", ""])
def test_quantity_rejected(admin, emp, q):
    r = apply(admin, q=q)
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert rows(admin) == []


def test_quantity_boundaries_accepted(admin, emp):
    assert apply(admin, q="1").status_code == 302
    assert apply(admin, q="30").status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "-5", "9.9", "x", ""])
def test_unit_price_rejected(admin, emp, p):
    assert apply(admin, p=p).status_code == 400
    assert rows(admin) == []


def test_unit_price_boundaries(admin, emp):
    assert apply(admin, p="1").status_code == 302
    assert apply(admin, p="100000").status_code == 302
    assert rows(admin)[1]["amount_incl_tax"] == 30 * 0 + 3 * 100000 * 110 // 100


def test_retired_and_unknown_employee(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert apply(admin, no="999999").status_code == 400
    assert rows(admin) == []


def test_approve_and_reject(admin, emp, make_employee):
    apply(admin)
    apply(admin)
    assert admin.post("/courier/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/courier/reject", data={"request_id": "2"}).status_code == 302
    assert [x["state"] for x in rows(admin)] == ["approved", "rejected"]


def test_only_pending_can_be_decided(admin, emp):
    apply(admin)
    admin.post("/courier/approve", data={"request_id": "1"})
    assert admin.post("/courier/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/courier/reject", data={"request_id": "1"}).status_code == 400
    assert rows(admin)[0]["state"] == "approved"


def test_unknown_request_id(admin, emp):
    assert admin.post("/courier/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/courier/reject", data={"request_id": "abc"}).status_code == 400


def test_self_approval_blocked_but_reject_allowed(admin, emp):
    apply(admin, no=ADMIN_NO)
    r = admin.post("/courier/approve", data={"request_id": "1"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"
    assert admin.post("/courier/reject", data={"request_id": "1"}).status_code == 302
    assert rows(admin)[0]["state"] == "rejected"


def test_employee_role_cannot_post(admin, emp, client):
    apply(admin)
    client.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert apply(client).status_code == 403
    assert client.post("/courier/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/courier/reject", data={"request_id": "1"}).status_code == 403
    assert rows(client)[0]["state"] == "pending"


def test_state_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, q="2", p="500")
    admin.post("/courier/reject", data={"request_id": "2"})
    body = admin.get("/courier/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in body and 'data-request-id="1"' not in body
    detail = admin.get("/courier/detail?request_id=2").get_data(as_text=True)
    assert "1000" in detail and "1100" in detail and "却下" in detail and "100001" in detail
    assert admin.get("/courier/?state=zzz").status_code == 400


def test_audit_log(admin, emp):
    apply(admin)
    apply(admin)
    admin.post("/courier/approve", data={"request_id": "1"})
    admin.post("/courier/reject", data={"request_id": "2"})
    apply(admin, q="0")  # 失敗は残さない
    logs = [(x["module"], x["action"], x["target"]) for x in admin.get("/audit.json").get_json()["rows"] if x["module"] == "courier"]
    assert logs == [("courier", "apply", "1"), ("courier", "apply", "2"), ("courier", "approve", "1"), ("courier", "reject", "2")]


def test_login_required(client):
    assert client.get("/courier/status.json").status_code == 302

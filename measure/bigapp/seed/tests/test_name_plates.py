"""名札の申請のテスト。総務規程 第 5・6・7 条のきまりを 1 つずつ確かめる。"""

import pytest

from app.core.db import ADMIN_NO
from app.modules.name_plates.domain import gross_amount


def apply(client, no="100001", q="3", p="333"):
    return client.post("/name_plates/apply", data={"employee_no": no, "quantity": q, "unit_price": p})


def listed(client):
    return client.get("/name_plates/status.json").get_json()["requests"]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_apply_success_and_json(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/name_plates/")
    assert listed(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]


@pytest.mark.parametrize("q,p,expected", [(1, 1, 1), (3, 333, 1098), (1, 99999, 109998), (100, 100000, 11000000), (1, 5, 5), (7, 13, 100)])
def test_gross_rounds_down(q, p, expected):
    assert gross_amount(q, p) == expected


def test_gross_truncates_fraction():
    assert gross_amount(1, 15) == 16  # 16.5 -> 16


@pytest.mark.parametrize("q", ["1", "100"])
def test_quantity_boundaries_ok(admin, emp, q):
    assert apply(admin, q=q).status_code == 302


@pytest.mark.parametrize("q", ["0", "101", "-1", "abc", "", "1.5"])
def test_quantity_out_of_range(admin, emp, q):
    r = apply(admin, q=q)
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert listed(admin) == []


@pytest.mark.parametrize("p", ["1", "100000"])
def test_price_boundaries_ok(admin, emp, p):
    assert apply(admin, p=p).status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "x", ""])
def test_price_out_of_range(admin, emp, p):
    assert apply(admin, p=p).status_code == 400
    assert listed(admin) == []


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert listed(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, no="999999").status_code == 400


def test_approve_and_reject(admin, make_employee):
    make_employee("100001")
    apply(admin)
    apply(admin)
    assert admin.post("/name_plates/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/name_plates/reject", data={"request_id": "2"}).status_code == 302
    assert [r["state"] for r in listed(admin)] == ["approved", "rejected"]


def test_decide_only_pending(admin, emp):
    apply(admin)
    admin.post("/name_plates/approve", data={"request_id": "1"})
    assert admin.post("/name_plates/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/name_plates/reject", data={"request_id": "1"}).status_code == 400
    assert listed(admin)[0]["state"] == "approved"


def test_unknown_request_id(admin):
    assert admin.post("/name_plates/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/name_plates/reject", data={"request_id": "abc"}).status_code == 400


def test_self_approval_blocked_but_reject_allowed(admin):
    apply(admin, no=ADMIN_NO)
    apply(admin, no=ADMIN_NO)
    r = admin.post("/name_plates/approve", data={"request_id": "1"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert listed(admin)[0]["state"] == "pending"
    assert admin.post("/name_plates/reject", data={"request_id": "2"}).status_code == 302
    assert listed(admin)[1]["state"] == "rejected"


def test_non_staff_cannot_post(client, admin, emp):
    admin.post("/employees/new", data={"employee_no": "100002", "name": "佐藤", "role": "employee"})
    apply(admin)
    client.post("/login", data={"employee_no": "100002", "password": "password1"})
    assert client.post("/name_plates/apply", data={"employee_no": "100001", "quantity": "1", "unit_price": "1"}).status_code == 403
    assert client.post("/name_plates/approve", data={"request_id": "1"}).status_code == 403
    assert client.get("/name_plates/status.json").status_code == 200


def test_login_required(client):
    assert client.get("/name_plates/").status_code == 302
    assert client.get("/name_plates/status.json").status_code == 302


def test_state_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, q="2", p="500")
    admin.post("/name_plates/reject", data={"request_id": "2"})
    html = admin.get("/name_plates/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    d = admin.get("/name_plates/detail?request_id=2").get_data(as_text=True)
    assert "1100" in d and "1000" in d and "100001" in d
    assert admin.get("/name_plates/detail?request_id=9").status_code == 404


def test_audit_log(admin, emp):
    apply(admin)
    apply(admin, q="0")  # 失敗は残さない
    admin.post("/name_plates/approve", data={"request_id": "1"})
    rows = admin.get("/audit.json").get_json()["rows"]
    assert [(r["module"], r["action"]) for r in rows if r["module"] == "name_plates"] == [("name_plates", "apply"), ("name_plates", "approve")]

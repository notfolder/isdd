"""切手の申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO, ADMIN_PASSWORD
from app.modules.stamps import gross_amount


def apply(client, no="100001", q="3", p="333"):
    return client.post("/stamps/apply", data={"employee_no": no, "quantity": q, "unit_price": p})


def status(client):
    return client.get("/stamps/status.json").get_json()["requests"]


def audit_rows(client):
    return [r for r in client.get("/audit.json").get_json()["rows"] if r["module"] == "stamps"]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_gross_amount_rounds_down():
    assert gross_amount(3, 333) == 1098  # 999 * 1.1 = 1098.9
    assert gross_amount(1, 1) == 1
    assert gross_amount(1, 9) == 9  # 9.9
    assert gross_amount(200, 100000) == 22000000


def test_apply_success_redirects_and_records(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/stamps/")
    assert status(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]
    assert [(a["action"], a["target"]) for a in audit_rows(admin)] == [("apply", "1")]


@pytest.mark.parametrize("q", ["1", "200"])
def test_quantity_boundaries_accepted(admin, emp, q):
    assert apply(admin, q=q).status_code == 302


@pytest.mark.parametrize("q", ["0", "201", "-1", "abc", "", "1.5"])
def test_quantity_invalid_rejected(admin, emp, q):
    r = apply(admin, q=q)
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert status(admin) == [] and audit_rows(admin) == []


@pytest.mark.parametrize("p", ["1", "100000"])
def test_unit_price_boundaries_accepted(admin, emp, p):
    assert apply(admin, p=p).status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "-5", "x", ""])
def test_unit_price_invalid_rejected(admin, emp, p):
    assert apply(admin, p=p).status_code == 400
    assert status(admin) == []


def test_unknown_employee_rejected(admin):
    r = apply(admin, no="999999")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert status(admin) == []


def test_approve_and_reject_by_staff(admin, emp):
    apply(admin)
    apply(admin)
    assert admin.post("/stamps/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/stamps/reject", data={"request_id": "2"}).status_code == 302
    assert [r["state"] for r in status(admin)] == ["approved", "rejected"]
    assert [a["action"] for a in audit_rows(admin)] == ["apply", "apply", "approve", "reject"]


def test_decide_only_pending(admin, emp):
    apply(admin)
    admin.post("/stamps/approve", data={"request_id": "1"})
    for action in ("approve", "reject"):
        r = admin.post(f"/stamps/{action}", data={"request_id": "1"})
        assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert status(admin)[0]["state"] == "approved"


def test_unknown_request_id_rejected(admin, emp):
    assert admin.post("/stamps/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/stamps/reject", data={"request_id": "abc"}).status_code == 400


def test_cannot_approve_own_request_but_can_reject(admin):
    apply(admin, no=ADMIN_NO)
    apply(admin, no=ADMIN_NO)
    r = admin.post("/stamps/approve", data={"request_id": "1"})
    assert r.status_code == 400
    assert status(admin)[0]["state"] == "pending"
    assert admin.post("/stamps/reject", data={"request_id": "2"}).status_code == 302
    assert status(admin)[1]["state"] == "rejected"


def test_non_staff_cannot_change_data(app, admin, emp):
    apply(admin)
    c = app.test_client()
    c.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert apply(c).status_code == 403
    assert c.post("/stamps/approve", data={"request_id": "1"}).status_code == 403
    assert c.post("/stamps/reject", data={"request_id": "1"}).status_code == 403
    assert len(status(c)) == 1 and status(c)[0]["state"] == "pending"


def test_anonymous_cannot_change_or_view(client):
    assert client.post("/stamps/apply", data={}).status_code == 302
    assert client.get("/stamps/status.json").status_code == 302


def test_list_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, q="2", p="500")
    admin.post("/stamps/reject", data={"request_id": "2"})
    html = admin.get("/stamps/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    d = admin.get("/stamps/detail?request_id=2").get_data(as_text=True)
    assert "1000" in d and "1100" in d and "却下" in d and "山田" in d
    assert admin.get("/stamps/detail?request_id=99").status_code == 404

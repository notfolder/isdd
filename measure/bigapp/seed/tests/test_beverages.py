"""来客用飲料の申請のテスト。"""

import pytest
from werkzeug.security import generate_password_hash

from app.core.db import get_db
from app.modules.beverages.models import with_tax


def apply(client, no="100001", quantity="3", unit_price="333"):
    return client.post("/beverages/apply", data={"employee_no": no, "quantity": quantity, "unit_price": unit_price})


def requests_json(client):
    return client.get("/beverages/status.json").get_json()["requests"]


def audit_rows(app):
    with app.app_context():
        return [dict(r) for r in get_db().execute("SELECT * FROM audit_log WHERE module = 'beverages' ORDER BY id")]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_apply_success_redirects_and_records(app, admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/beverages/")
    assert requests_json(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]
    rows = audit_rows(app)
    assert [(x["action"], x["target"]) for x in rows] == [("apply", "1")]


def test_tax_rounds_down():
    assert with_tax(3, 333) == 1098  # 1098.9 を切り捨て
    assert with_tax(1, 1) == 1  # 1.1 を切り捨て
    assert with_tax(50, 100000) == 5500000


@pytest.mark.parametrize("q,ok", [("0", False), ("1", True), ("50", True), ("51", False), ("-1", False), ("1.5", False), ("abc", False), ("", False)])
def test_quantity_boundaries(admin, emp, q, ok):
    r = apply(admin, quantity=q)
    assert (r.status_code == 302) == ok
    if not ok:
        assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
        assert requests_json(admin) == []


@pytest.mark.parametrize("p,ok", [("0", False), ("1", True), ("100000", True), ("100001", False), ("x", False), ("", False)])
def test_unit_price_boundaries(admin, emp, p, ok):
    r = apply(admin, unit_price=p)
    assert (r.status_code == 302) == ok
    if not ok:
        assert r.status_code == 400 and requests_json(admin) == []


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    r = apply(admin)
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert requests_json(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, no="999999").status_code == 400


def test_non_staff_cannot_post(app, client, admin, make_employee):
    make_employee("100002", "一般")
    with app.app_context():
        pass
    admin.post("/logout")
    # 一般社員のパスワードは既定の password1
    client.post("/login", data={"employee_no": "100002", "password": "password1"})
    assert apply(client, no="100002").status_code == 403
    assert client.post("/beverages/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/beverages/reject", data={"request_id": "1"}).status_code == 403
    assert requests_json(client) == []


def test_login_required(client):
    assert client.get("/beverages/").status_code == 302
    assert client.get("/beverages/status.json").status_code == 302


def test_approve_by_other_staff(app, admin, make_employee):
    make_employee("100001", "山田", role="staff")
    apply(admin, no="100001")  # 申請者は 100001、承認者は管理者
    r = admin.post("/beverages/approve", data={"request_id": "1"})
    assert r.status_code == 302
    assert requests_json(admin)[0]["state"] == "approved"
    assert [x["action"] for x in audit_rows(app)] == ["apply", "approve"]


def test_self_approval_rejected_but_self_reject_allowed(app, admin, make_employee):
    from app.core.db import ADMIN_NO

    apply(admin, no=ADMIN_NO)
    apply(admin, no=ADMIN_NO)
    r = admin.post("/beverages/approve", data={"request_id": "1"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert requests_json(admin)[0]["state"] == "pending"
    assert [x["action"] for x in audit_rows(app)] == ["apply", "apply"]
    assert admin.post("/beverages/reject", data={"request_id": "1"}).status_code == 302
    assert requests_json(admin)[0]["state"] == "rejected"


def test_only_pending_can_be_decided(admin, emp):
    apply(admin)
    apply(admin)
    admin.post("/beverages/approve", data={"request_id": "1"})
    admin.post("/beverages/reject", data={"request_id": "2"})
    for action in ("approve", "reject"):
        for rid in ("1", "2"):
            assert admin.post(f"/beverages/{action}", data={"request_id": rid}).status_code == 400
    assert [r["state"] for r in requests_json(admin)] == ["approved", "rejected"]


def test_unknown_request_id(admin, emp):
    assert admin.post("/beverages/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/beverages/reject", data={"request_id": "x"}).status_code == 400


def test_reject_records_audit(app, admin, emp):
    apply(admin)
    admin.post("/beverages/reject", data={"request_id": "1"})
    assert [(x["action"], x["target"]) for x in audit_rows(app)] == [("apply", "1"), ("reject", "1")]


def test_index_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, quantity="5", unit_price="100")
    admin.post("/beverages/reject", data={"request_id": "2"})
    html = admin.get("/beverages/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    detail = admin.get("/beverages/detail?request_id=2").get_data(as_text=True)
    assert "550" in detail and "500" in detail and "100001" in detail
    assert admin.get("/beverages/detail?request_id=99").status_code == 404

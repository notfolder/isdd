"""社章の申請のテスト。総務規程 第 5〜7 条と依頼のきまりを 1 つずつ確かめる。"""

import pytest

from app.core.db import ADMIN_NO, ADMIN_PASSWORD
from app.modules.badges.service import tax_included


def apply(client, no="100001", quantity="3", unit_price="333"):
    return client.post("/badges/apply", data={"employee_no": no, "quantity": quantity, "unit_price": unit_price})


def requests_json(client):
    return client.get("/badges/status.json").get_json()["requests"]


def audit_rows(admin):
    return admin.get("/audit.json").get_json()["rows"]


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def test_apply_ok_redirects_and_records(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/badges/")
    assert requests_json(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]
    assert [x for x in audit_rows(admin) if x["module"] == "badges"][0]["action"] == "apply"


@pytest.mark.parametrize("q,p,expected", [(1, 1, 1), (3, 333, 1098), (1, 9, 9), (7, 101, 777), (50, 100000, 5500000), (1, 5, 5)])
def test_tax_included_floors(q, p, expected):
    assert tax_included(q, p) == expected


def test_tax_floor_amount_saved(admin, emp):
    apply(admin, quantity="1", unit_price="99")  # 108.9 -> 108
    assert requests_json(admin)[0]["amount_incl_tax"] == 108


@pytest.mark.parametrize("q", ["1", "50"])
def test_quantity_boundaries_ok(admin, emp, q):
    assert apply(admin, quantity=q).status_code == 302


@pytest.mark.parametrize("q", ["0", "51", "-1", "1.5", "abc", ""])
def test_quantity_invalid(admin, emp, q):
    r = apply(admin, quantity=q)
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert requests_json(admin) == []


@pytest.mark.parametrize("p", ["1", "100000"])
def test_unit_price_boundaries_ok(admin, emp, p):
    assert apply(admin, unit_price=p).status_code == 302


@pytest.mark.parametrize("p", ["0", "100001", "-5", "10.5", "x", ""])
def test_unit_price_invalid(admin, emp, p):
    assert apply(admin, unit_price=p).status_code == 400
    assert requests_json(admin) == []


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert requests_json(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, no="999999").status_code == 400


def test_non_staff_cannot_post(client, make_employee):
    make_employee("100002", "佐藤")
    # 一般社員でログイン
    from werkzeug.security import generate_password_hash  # noqa: F401
    import sqlite3
    db = sqlite3.connect(client.application.config["DATABASE"])
    db.execute("UPDATE employees SET password_hash = ? WHERE employee_no = '100002'", (generate_password_hash("pw"),))
    db.commit()
    db.close()
    client.post("/logout")
    client.post("/login", data={"employee_no": "100002", "password": "pw"})
    assert apply(client, no="100002").status_code == 403
    assert client.post("/badges/approve", data={"request_id": "1"}).status_code == 403
    assert client.post("/badges/reject", data={"request_id": "1"}).status_code == 403
    assert client.get("/badges/status.json").status_code == 200


def test_approve_by_other_staff(admin, make_employee):
    make_employee("100003", "総務二", role="staff")
    apply(admin, no="100003")  # 申請者は別の担当者、承認者は管理者
    r = admin.post("/badges/approve", data={"request_id": "1"})
    assert r.status_code == 302
    assert requests_json(admin)[0]["state"] == "approved"
    assert any(x["action"] == "approve" for x in audit_rows(admin))


def test_self_approve_rejected_but_reject_allowed(admin):
    apply(admin, no=ADMIN_NO)
    r = admin.post("/badges/approve", data={"request_id": "1"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert requests_json(admin)[0]["state"] == "pending"
    assert not any(x["action"] == "approve" for x in audit_rows(admin))
    assert admin.post("/badges/reject", data={"request_id": "1"}).status_code == 302
    assert requests_json(admin)[0]["state"] == "rejected"
    assert any(x["action"] == "reject" for x in audit_rows(admin))


def test_only_pending_can_be_decided(admin, emp):
    apply(admin)
    admin.post("/badges/approve", data={"request_id": "1"})
    assert admin.post("/badges/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/badges/reject", data={"request_id": "1"}).status_code == 400
    apply(admin)
    admin.post("/badges/reject", data={"request_id": "2"})
    assert admin.post("/badges/approve", data={"request_id": "2"}).status_code == 400
    assert [x["state"] for x in requests_json(admin)] == ["approved", "rejected"]


@pytest.mark.parametrize("rid", ["99", "abc", ""])
def test_unknown_request_id(admin, rid):
    assert admin.post("/badges/approve", data={"request_id": rid}).status_code == 400
    assert admin.post("/badges/reject", data={"request_id": rid}).status_code == 400


def test_list_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, quantity="2", unit_price="100")
    admin.post("/badges/reject", data={"request_id": "2"})
    html = admin.get("/badges/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    d = admin.get("/badges/detail?request_id=2").get_data(as_text=True)
    assert "200" in d and "220" in d and "却下" in d and "100001" in d
    assert admin.get("/badges/detail?request_id=9").status_code == 404
    assert admin.get("/badges/?state=bogus").status_code == 400


def test_login_required(client):
    assert client.get("/badges/status.json").status_code == 302
    assert client.get("/badges/").status_code == 302

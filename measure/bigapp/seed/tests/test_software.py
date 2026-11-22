"""ソフトウェア購入申請のテスト。"""

import pytest

from app.core.db import ADMIN_NO
from app.modules.software.logic import total


def apply(client, no="100001", q="1", p="100"):
    return client.post("/software/apply", data={"employee_no": no, "quantity": q, "unit_price": p})


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def state_of(client, rid=1):
    reqs = client.get("/software/status.json").get_json()["requests"]
    return next(r["state"] for r in reqs if r["id"] == rid)


def test_apply_success(admin, emp):
    r = apply(admin, q="3", p="333")
    assert r.status_code == 302 and r.headers["Location"].endswith("/software/")
    item = admin.get("/software/status.json").get_json()["requests"][0]
    assert item == {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}


@pytest.mark.parametrize("q,ok", [("0", False), ("1", True), ("10", True), ("11", False), ("-1", False), ("1.5", False), ("", False), ("abc", False)])
def test_quantity_bounds(admin, emp, q, ok):
    assert (apply(admin, q=q).status_code == 302) is ok


@pytest.mark.parametrize("p,ok", [("0", False), ("1", True), ("100000", True), ("100001", False), ("x", False), ("", False)])
def test_unit_price_bounds(admin, emp, p, ok):
    assert (apply(admin, p=p).status_code == 302) is ok


def test_invalid_input_shows_error_and_keeps_data(admin, emp):
    r = apply(admin, q="11")
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert admin.get("/software/status.json").get_json()["requests"] == []


def test_total_rounds_down():
    assert total(1, 1) == 1  # 税額 0.1 円は切り捨て
    assert total(1, 9) == 9
    assert total(1, 10) == 11
    assert total(3, 333) == 1098
    assert total(10, 100000) == 1100000


def test_total_in_status(admin, emp):
    apply(admin, q="1", p="19")  # 税額 1.9 -> 1
    assert admin.get("/software/status.json").get_json()["requests"][0]["amount_incl_tax"] == 20


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400


def test_unknown_employee_rejected(admin):
    assert apply(admin, no="999999").status_code == 400


def test_approve(admin, emp):
    apply(admin)
    r = admin.post("/software/approve", data={"request_id": "1"})
    assert r.status_code == 302
    assert state_of(admin) == "approved"


def test_reject(admin, emp):
    apply(admin)
    assert admin.post("/software/reject", data={"request_id": "1"}).status_code == 302
    assert state_of(admin) == "rejected"


def test_cannot_approve_twice_or_after_reject(admin, emp):
    apply(admin)
    admin.post("/software/approve", data={"request_id": "1"})
    assert admin.post("/software/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/software/reject", data={"request_id": "1"}).status_code == 400
    assert state_of(admin) == "approved"


def test_cannot_approve_rejected(admin, emp):
    apply(admin)
    admin.post("/software/reject", data={"request_id": "1"})
    assert admin.post("/software/approve", data={"request_id": "1"}).status_code == 400
    assert state_of(admin) == "rejected"


def test_self_approval_forbidden_but_reject_ok(admin):
    apply(admin, no=ADMIN_NO)
    r = admin.post("/software/approve", data={"request_id": "1"})
    assert r.status_code == 400 and 'class="error"' in r.get_data(as_text=True)
    assert state_of(admin) == "pending"
    assert admin.post("/software/reject", data={"request_id": "1"}).status_code == 302
    assert state_of(admin) == "rejected"


def test_unknown_request_id(admin, emp):
    assert admin.post("/software/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/software/reject", data={"request_id": "abc"}).status_code == 400


def test_post_requires_staff(admin, make_employee, client):
    make_employee("100002", "佐藤")
    client.post("/logout")
    # 一般社員でログインする（初期パスワードは password1）
    client.post("/login", data={"employee_no": "100002", "password": "password1"})
    assert apply(client).status_code == 403
    assert client.post("/software/approve", data={"request_id": "1"}).status_code == 403
    assert client.get("/software/").status_code == 200  # 閲覧はできる


def test_login_required(client):
    assert client.get("/software/").status_code == 302
    assert client.get("/software/status.json").status_code == 302


def test_audit_recorded(admin, emp):
    apply(admin)
    apply(admin)
    admin.post("/software/approve", data={"request_id": "1"})
    admin.post("/software/reject", data={"request_id": "2"})
    rows = [r for r in admin.get("/audit.json").get_json()["rows"] if r["module"] == "software"]
    assert [r["action"] for r in rows] == ["apply", "apply", "approve", "reject"]
    assert rows[2]["target"] == "1"


def test_failed_operation_not_audited(admin, emp):
    apply(admin, q="0")
    assert [r for r in admin.get("/audit.json").get_json()["rows"] if r["module"] == "software"] == []


def test_index_filter_and_detail(admin, emp):
    apply(admin)
    apply(admin, q="2", p="50")
    admin.post("/software/reject", data={"request_id": "2"})
    page = admin.get("/software/?state=rejected").get_data(as_text=True)
    assert "<td>50</td>" in page and "<td>100</td>" not in page
    d = admin.get("/software/detail?request_id=2").get_data(as_text=True)
    assert "110" in d and "100" in d and "山田" in d and "rejected" in d
    assert admin.get("/software/detail?request_id=99").status_code == 404

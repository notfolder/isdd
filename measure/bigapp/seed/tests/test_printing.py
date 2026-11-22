"""印刷の申請のテスト。総務規程 第 5〜7 条のきまりを 1 つずつ確かめる。"""

import pytest

from app.core.db import get_db
from app.modules.printing.rules import with_tax


def apply(client, employee="100001", quantity="3", unit_price="333"):
    return client.post("/printing/apply", data={"employee_no": employee, "quantity": quantity, "unit_price": unit_price})


def login(client, number, password="password1"):
    client.post("/logout")
    return client.post("/login", data={"employee_no": number, "password": password})


def statuses(client):
    return client.get("/printing/status.json").get_json()["requests"]


@pytest.fixture
def worker(make_employee):
    return make_employee("100001", "山田")


def test_apply_success_redirects_and_records(admin, worker, app):
    response = apply(admin)
    assert response.status_code == 302 and response.headers["Location"].endswith("/printing/")
    assert statuses(admin) == [
        {"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}
    ]


def test_tax_rounds_down():
    assert with_tax(3, 333) == 1098  # 999 * 1.1 = 1098.9 -> 1098
    assert with_tax(1, 1) == 1  # 1.1 -> 1
    assert with_tax(1000, 100000) == 110000000


def test_tax_shown_in_detail(admin, worker):
    apply(admin, quantity="3", unit_price="333")
    page = admin.get("/printing/detail?request_id=1").get_data(as_text=True)
    assert "1098" in page and "999" in page and "100001" in page


@pytest.mark.parametrize("quantity,ok", [("0", False), ("1", True), ("1000", True), ("1001", False), ("-1", False), ("1.5", False), ("abc", False), ("", False)])
def test_quantity_boundaries(admin, worker, quantity, ok):
    response = apply(admin, quantity=quantity)
    assert response.status_code == (302 if ok else 400)
    assert len(statuses(admin)) == (1 if ok else 0)


@pytest.mark.parametrize("price,ok", [("0", False), ("1", True), ("100000", True), ("100001", False), ("-5", False), ("2.5", False), ("x", False), ("", False)])
def test_unit_price_boundaries(admin, worker, price, ok):
    response = apply(admin, unit_price=price)
    assert response.status_code == (302 if ok else 400)
    assert len(statuses(admin)) == (1 if ok else 0)


def test_error_is_shown_in_error_element(admin, worker):
    response = apply(admin, quantity="0")
    assert response.status_code == 400
    assert '<p class="error">' in response.get_data(as_text=True)


def test_retired_employee_rejected(admin, worker):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert statuses(admin) == []


def test_unknown_employee_rejected(admin):
    assert apply(admin, employee="999999").status_code == 400


def test_approve_by_other_staff(admin, worker, make_employee):
    make_employee("200001", "別の担当者", role="staff")
    apply(admin, employee="100001")
    login(admin, "200001")
    response = admin.post("/printing/approve", data={"request_id": "1"})
    assert response.status_code == 302
    assert statuses(admin)[0]["state"] == "approved"


def test_staff_cannot_approve_own_request(admin, make_employee):
    make_employee("200001", "担当者", role="staff")
    login(admin, "200001")
    apply(admin, employee="200001")
    response = admin.post("/printing/approve", data={"request_id": "1"})
    assert response.status_code == 400 and '<p class="error">' in response.get_data(as_text=True)
    assert statuses(admin)[0]["state"] == "pending"


def test_staff_can_reject_own_request(admin, make_employee):
    make_employee("200001", "担当者", role="staff")
    login(admin, "200001")
    apply(admin, employee="200001")
    assert admin.post("/printing/reject", data={"request_id": "1"}).status_code == 302
    assert statuses(admin)[0]["state"] == "rejected"


def test_cannot_decide_twice(admin, worker, make_employee):
    apply(admin)
    assert admin.post("/printing/approve", data={"request_id": "1"}).status_code == 302
    assert admin.post("/printing/approve", data={"request_id": "1"}).status_code == 400
    assert admin.post("/printing/reject", data={"request_id": "1"}).status_code == 400
    assert statuses(admin)[0]["state"] == "approved"


def test_cannot_approve_rejected(admin, worker):
    apply(admin)
    admin.post("/printing/reject", data={"request_id": "1"})
    assert admin.post("/printing/approve", data={"request_id": "1"}).status_code == 400
    assert statuses(admin)[0]["state"] == "rejected"


def test_unknown_request_id_rejected(admin, worker):
    assert admin.post("/printing/approve", data={"request_id": "99"}).status_code == 400
    assert admin.post("/printing/reject", data={"request_id": "abc"}).status_code == 400


def test_non_staff_cannot_post(admin, worker):
    apply(admin)
    login(admin, "100001")
    assert apply(admin).status_code == 403
    assert admin.post("/printing/approve", data={"request_id": "1"}).status_code == 403
    assert admin.post("/printing/reject", data={"request_id": "1"}).status_code == 403
    assert len(statuses(admin)) == 1 and statuses(admin)[0]["state"] == "pending"


def test_anonymous_post_redirects_to_login(app, worker):
    response = apply(app.test_client())
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_employee_can_read_status_and_list(admin, worker):
    apply(admin)
    login(admin, "100001")
    assert admin.get("/printing/status.json").status_code == 200
    assert admin.get("/printing/").status_code == 200
    assert admin.get("/printing/detail?request_id=1").status_code == 200


def test_state_filter(admin, worker):
    apply(admin, quantity="11")
    apply(admin, quantity="22")
    admin.post("/printing/reject", data={"request_id": "2"})
    page = admin.get("/printing/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in page and 'data-request-id="1"' not in page


def test_status_json_sorted_by_id(admin, worker):
    for q in ("1", "2", "3"):
        apply(admin, quantity=q)
    assert [r["id"] for r in statuses(admin)] == [1, 2, 3]


def test_audit_log_for_each_operation(admin, worker):
    apply(admin)
    apply(admin)
    admin.post("/printing/approve", data={"request_id": "1"})
    admin.post("/printing/reject", data={"request_id": "2"})
    apply(admin, quantity="0")  # 受け付けない操作は残さない
    with admin.application.app_context():
        rows = get_db().execute("SELECT action, target FROM audit_log WHERE module = 'printing' ORDER BY id").fetchall()
    assert [(r["action"], r["target"]) for r in rows] == [("apply", "1"), ("apply", "2"), ("approve", "1"), ("reject", "2")]


def test_detail_unknown_is_404(admin):
    assert admin.get("/printing/detail?request_id=5").status_code == 404

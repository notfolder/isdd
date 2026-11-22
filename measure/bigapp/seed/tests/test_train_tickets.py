"""乗車券の申請のテスト。"""

import pytest

from app.modules.train_tickets import domain

URL = "/train_tickets"


def apply(client, number="100001", quantity="3", unit_price="333"):
    return client.post(f"{URL}/apply", data={"employee_no": number, "quantity": quantity, "unit_price": unit_price})


@pytest.fixture
def emp(make_employee):
    return make_employee("100001", "山田")


def rows(client):
    return client.get(f"{URL}/status.json").get_json()["requests"]


def audit_actions(client):
    return [(r["module"], r["action"], r["target"]) for r in client.get("/audit.json").get_json()["rows"]]


def test_tax_included_rounds_down():
    assert domain.tax_included(3, 333) == 1098
    assert domain.tax_included(1, 1) == 1  # 1.1 円は切り捨て
    assert domain.tax_included(1, 9) == 9  # 9.9 円は切り捨て
    assert domain.tax_included(40, 100000) == 4400000


def test_apply_success_redirects_and_records(admin, emp):
    r = apply(admin)
    assert r.status_code == 302 and r.headers["Location"].endswith("/train_tickets/")
    assert rows(admin) == [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"}]
    assert ("train_tickets", "apply", "1") in audit_actions(admin)


@pytest.mark.parametrize("q,ok", [("0", False), ("1", True), ("40", True), ("41", False), ("-1", False), ("1.5", False), ("", False), ("abc", False)])
def test_quantity_boundaries(admin, emp, q, ok):
    r = apply(admin, quantity=q)
    assert r.status_code == (302 if ok else 400)
    if not ok:
        assert '<p class="error">' in r.get_data(as_text=True)
        assert rows(admin) == []


@pytest.mark.parametrize("p,ok", [("0", False), ("1", True), ("100000", True), ("100001", False), ("-5", False), ("1e3", False), ("", False)])
def test_unit_price_boundaries(admin, emp, p, ok):
    assert apply(admin, unit_price=p).status_code == (302 if ok else 400)
    assert len(rows(admin)) == (1 if ok else 0)


def test_unknown_employee_rejected(admin):
    r = apply(admin, number="999999")
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin) == []


def test_retired_employee_rejected(admin, emp):
    admin.post("/employees/retire", data={"employee_no": "100001"})
    assert apply(admin).status_code == 400
    assert rows(admin) == []


def test_apply_requires_staff(client, admin, emp):
    admin.post("/logout")
    assert client.post(f"{URL}/apply", data={"employee_no": "100001", "quantity": "1", "unit_price": "1"}).status_code == 302  # ログインへ
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    assert apply(client).status_code == 403
    assert client.post(f"{URL}/approve", data={"request_id": "1"}).status_code == 403
    assert client.post(f"{URL}/reject", data={"request_id": "1"}).status_code == 403


def test_approve_by_other_staff(admin, make_employee):
    make_employee("100001", "山田")
    make_employee("100002", "佐藤", role="staff")
    apply(admin, "100001")
    r = admin.post(f"{URL}/approve", data={"request_id": "1"})  # admin(900001) は申請者ではない
    assert r.status_code == 302 and r.headers["Location"].endswith("/train_tickets/")
    assert rows(admin)[0]["state"] == "approved"
    assert ("train_tickets", "approve", "1") in audit_actions(admin)


def test_self_approval_forbidden_but_reject_allowed(admin):
    apply(admin, "900001")
    r = admin.post(f"{URL}/approve", data={"request_id": "1"})
    assert r.status_code == 400 and '<p class="error">' in r.get_data(as_text=True)
    assert rows(admin)[0]["state"] == "pending"
    assert ("train_tickets", "approve", "1") not in audit_actions(admin)
    assert admin.post(f"{URL}/reject", data={"request_id": "1"}).status_code == 302
    assert rows(admin)[0]["state"] == "rejected"
    assert ("train_tickets", "reject", "1") in audit_actions(admin)


def test_only_pending_can_change(admin, emp):
    apply(admin)
    apply(admin)
    admin.post(f"{URL}/approve", data={"request_id": "1"})
    admin.post(f"{URL}/reject", data={"request_id": "2"})
    for action in ("approve", "reject"):
        for i in ("1", "2"):
            assert admin.post(f"{URL}/{action}", data={"request_id": i}).status_code == 400
    assert [r["state"] for r in rows(admin)] == ["approved", "rejected"]


@pytest.mark.parametrize("action", ["approve", "reject"])
@pytest.mark.parametrize("rid", ["99", "abc", ""])
def test_unknown_request_id(admin, emp, action, rid):
    assert admin.post(f"{URL}/{action}", data={"request_id": rid}).status_code == 400


def test_state_filter_and_index(admin, emp):
    apply(admin)
    apply(admin, quantity="2")
    admin.post(f"{URL}/reject", data={"request_id": "2"})
    html = admin.get(f"{URL}/?state=rejected").get_data(as_text=True)
    assert 'data-request-id="2"' in html and 'data-request-id="1"' not in html
    html = admin.get(f"{URL}/").get_data(as_text=True)
    assert 'data-request-id="1"' in html and 'data-request-id="2"' in html


def test_detail_page(admin, emp):
    apply(admin)
    html = admin.get(f"{URL}/detail?request_id=1").get_data(as_text=True)
    for text in ("333", "999", "1098", "100001", "申請中"):
        assert text in html
    assert admin.get(f"{URL}/detail?request_id=5").status_code == 400


def test_login_required_for_views(client):
    for path in ("/", "/detail?request_id=1", "/status.json"):
        assert client.get(URL + path).status_code == 302


def test_status_json_visible_to_employee_and_ordered(client, admin, emp):
    apply(admin)
    apply(admin, quantity="1", unit_price="9")
    admin.post("/logout")
    client.post("/login", data={"employee_no": "100001", "password": "password1"})
    data = rows(client)
    assert [r["id"] for r in data] == [1, 2] and data[1]["amount_incl_tax"] == 9

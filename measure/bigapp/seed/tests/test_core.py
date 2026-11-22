from app.core.db import ADMIN_NO


def test_login_required(client):
    assert client.get("/").status_code == 302


def test_admin_can_register_and_retire_employee(admin, make_employee):
    make_employee("100001", "山田 太郎")
    rows = admin.get("/employees.json").get_json()["employees"]
    assert {r["employee_no"] for r in rows} == {ADMIN_NO, "100001"}
    admin.post("/employees/retire", data={"employee_no": "100001"})
    rows = {r["employee_no"]: r for r in admin.get("/employees.json").get_json()["employees"]}
    assert rows["100001"]["status"] == "retired"
    audit = admin.get("/audit.json").get_json()["rows"]
    assert [(r["module"], r["action"], r["target"]) for r in audit] == [("employees", "create", "100001"), ("employees", "retire", "100001")]


def test_duplicate_employee_is_rejected(admin, make_employee):
    make_employee("100001")
    assert admin.post("/employees/new", data={"employee_no": "100001", "name": "別人"}).status_code == 400

"""画面（Flask のテストクライアント）の結合テスト。"""

import time

import pytest

from equipment_ledger.web import create_app


def make_client(tmp_path, idle_timeout=1800):
    app = create_app({"data_dir": tmp_path, "idle_timeout_seconds": idle_timeout})
    app.config["TESTING"] = True
    return app.test_client()


def register(client, number, name="名前", password="password1"):
    return client.post(
        "/accounts/register/",
        data={"employee_number": number, "name": name, "password": password},
    )


def login(client, number, password="password1"):
    return client.post("/login/", data={"employee_number": number, "password": password})


def test_top_page_anonymous_shows_links_and_no_buttons(tmp_path):
    client = make_client(tmp_path)
    html = client.get("/").get_data(as_text=True)
    assert "備品は登録されていません" in html
    assert 'href="/login/"' in html and 'href="/accounts/register/"' in html
    assert "ログアウト" not in html


def test_first_registration_is_manager_and_sees_register_link(tmp_path):
    client = make_client(tmp_path)
    response = register(client, "123456", "山田太郎")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login/")
    login(client, "123456")
    html = client.get("/").get_data(as_text=True)
    assert "山田太郎" in html and "備品を登録" in html


def test_employee_has_no_manager_actions(tmp_path):
    client = make_client(tmp_path)
    register(client, "123456")
    register(client, "234567")
    login(client, "123456")
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})
    client.post("/logout/")
    login(client, "234567")
    html = client.get("/").get_data(as_text=True)
    assert "備品を登録" not in html
    assert ">修正<" not in html and ">削除<" not in html


def test_login_failure_message_does_not_reveal_which_is_wrong(tmp_path):
    client = make_client(tmp_path)
    register(client, "123456")
    wrong_password = login(client, "123456", "bad-pass").get_data(as_text=True)
    wrong_number = login(client, "999999").get_data(as_text=True)
    assert "社員番号またはパスワードが違います" in wrong_password
    assert "社員番号またはパスワードが違います" in wrong_number


@pytest.mark.parametrize(
    "method,path,data",
    [
        ("get", "/equipment/new/", None),
        ("post", "/equipment/new/", {"equipment_number": "A-1", "name": "x"}),
        ("get", "/equipment/A-1/edit/", None),
        ("post", "/equipment/A-1/edit/", {"equipment_number": "A-2", "name": "y"}),
        ("post", "/equipment/A-1/delete/", None),
    ],
)
def test_anonymous_requests_are_refused(tmp_path, method, path, data):
    client = make_client(tmp_path)
    register(client, "123456")
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})  # 未ログインなので無視される
    response = getattr(client, method)(path, data=data)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login/")
    html = client.get("/login/").get_data(as_text=True)
    assert "この操作は担当者だけが行えます" in html


def test_employee_requests_are_refused_and_data_unchanged(tmp_path):
    client = make_client(tmp_path)
    register(client, "123456")
    register(client, "234567")
    login(client, "123456")
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})
    client.post("/logout/")
    login(client, "234567")
    response = client.post("/equipment/A-1/delete/")
    assert response.headers["Location"].endswith("/")
    html = client.get("/").get_data(as_text=True)
    assert "この操作は担当者だけが行えます" in html
    assert 'data-equipment-number="A-1"' in html


def test_idle_timeout_logs_out(tmp_path):
    client = make_client(tmp_path, idle_timeout=1)
    register(client, "123456", "山田太郎")
    login(client, "123456")
    assert "山田太郎" in client.get("/").get_data(as_text=True)
    time.sleep(1.2)
    html = client.get("/").get_data(as_text=True)
    assert "セッションの有効期限が切れました。ログインしてください" in html
    assert "山田太郎" not in html


def test_equipment_crud_as_manager(tmp_path):
    client = make_client(tmp_path)
    register(client, "123456")
    login(client, "123456")
    assert client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "旧"}).status_code == 302
    html = client.get("/").get_data(as_text=True)
    assert 'data-equipment-number="A-1"' in html and "旧" in html
    client.post("/equipment/A-1/edit/", data={"equipment_number": "A-1", "name": "新"})
    assert "新" in client.get("/").get_data(as_text=True)
    client.post("/equipment/A-1/delete/")
    assert "備品は登録されていません" in client.get("/").get_data(as_text=True)


def test_form_errors_keep_input(tmp_path):
    client = make_client(tmp_path)
    register(client, "123456")
    login(client, "123456")
    html = client.post("/equipment/new/", data={"equipment_number": "PC 1", "name": "残す名前"}).get_data(as_text=True)
    assert "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください" in html
    assert 'value="残す名前"' in html

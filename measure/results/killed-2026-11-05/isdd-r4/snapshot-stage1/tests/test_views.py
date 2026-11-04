"""画面と操作の結合テスト（Flask のテストクライアント）。契約の id・文言を確かめる。"""

from app import accounts


def _register(client, number, name, password="password1"):
    return client.post(
        "/accounts/register/",
        data={"employee_number": number, "name": name, "password": password},
        follow_redirects=True,
    )


def _login(client, number, password="password1"):
    return client.post("/login/", data={"employee_number": number, "password": password}, follow_redirects=True)


def test_index_is_public_and_shows_empty_message(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "備品は登録されていません" in body
    assert 'href="/login/"' in body and 'href="/accounts/register/"' in body


def test_first_registration_message_and_manager_login(client):
    response = _register(client, "000001", "山田太郎")
    body = response.get_data(as_text=True)
    assert "登録しました。ログインしてください" in body
    response = _login(client, "000001")
    body = response.get_data(as_text=True)
    assert 'class="current-user"' in body and "山田太郎" in body
    assert "備品を登録" in body


def test_login_failure_shows_one_message(client):
    _register(client, "000001", "山田太郎")
    wrong_password = client.post("/login/", data={"employee_number": "000001", "password": "x"}).get_data(as_text=True)
    unknown_user = client.post("/login/", data={"employee_number": "999999", "password": "password1"}).get_data(as_text=True)
    assert 'class="error">社員番号またはパスワードが違います' in wrong_password
    assert 'class="error">社員番号またはパスワードが違います' in unknown_user


def test_registration_field_errors_keep_values(client):
    response = client.post(
        "/accounts/register/",
        data={"employee_number": "12345", "name": "", "password": "short"},
    )
    body = response.get_data(as_text=True)
    assert 'class="field-error">社員番号は 6 桁の数字で入力してください' in body
    assert 'class="field-error">名前を入力してください' in body
    assert 'class="field-error">パスワードは 8 文字以上で入力してください' in body
    assert 'value="12345"' in body


def test_employee_cannot_use_manager_pages(client):
    _register(client, "000001", "担当")
    _register(client, "000002", "社員")
    _login(client, "000002")
    response = client.get("/equipment/new/")
    assert response.status_code == 302
    page = client.get("/")
    body = page.get_data(as_text=True)
    assert "この操作は担当者だけが行えます" in body
    assert 'class="message"' in body


def test_manager_creates_updates_and_deletes(client):
    _register(client, "000001", "担当")
    _login(client, "000001")
    client.post("/equipment/new/", data={"equipment_number": "EQ-1", "name": "机"}, follow_redirects=True)
    body = client.get("/").get_data(as_text=True)
    assert 'data-equipment-number="EQ-1"' in body
    assert "修正" in body and "削除" in body
    client.post("/equipment/EQ-1/edit/", data={"equipment_number": "EQ-1", "name": "椅子"}, follow_redirects=True)
    assert "椅子" in client.get("/").get_data(as_text=True)
    client.post("/equipment/EQ-1/delete/", follow_redirects=True)
    assert "備品は登録されていません" in client.get("/").get_data(as_text=True)


def test_logout_clears_session(client):
    _register(client, "000001", "担当")
    _login(client, "000001")
    client.post("/logout/")
    body = client.get("/").get_data(as_text=True)
    assert 'class="current-user"' not in body
    assert 'href="/login/"' in body


def test_anonymous_post_to_manager_action_redirects_to_login(client):
    response = client.post("/equipment/EQ-1/delete/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login/")

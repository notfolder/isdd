"""画面（Flask のテストクライアント）の結合テスト。"""

import re
import time

import pytest

from equipment_ledger.web import create_app

MANAGER = "1234567"
EMPLOYEE = "2345678"


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


def borrower_option_value(html, name, number):
    match = re.search(r'<option value="(\d+)"[^>]*>' + re.escape(f"{name}（{number}）"), html)
    assert match, "借りる社員の選択肢が見つかりません"
    return match.group(1)


def test_top_page_anonymous_shows_links_and_no_buttons(tmp_path):
    client = make_client(tmp_path)
    html = client.get("/").get_data(as_text=True)
    assert "備品は登録されていません" in html
    assert 'href="/login/"' in html and 'href="/accounts/register/"' in html
    assert "ログアウト" not in html


def test_first_registration_is_manager_and_sees_register_link(tmp_path):
    client = make_client(tmp_path)
    response = register(client, MANAGER, "山田太郎")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login/")
    login(client, MANAGER)
    html = client.get("/").get_data(as_text=True)
    assert "山田太郎" in html and "備品を登録" in html


def test_six_digit_employee_number_is_refused(tmp_path):
    client = make_client(tmp_path)
    html = register(client, "123456", "山田太郎").get_data(as_text=True)
    assert "社員番号は 7 桁の数字で入力してください" in html


def test_employee_has_no_manager_actions(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER)
    register(client, EMPLOYEE)
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})
    client.post("/logout/")
    login(client, EMPLOYEE)
    html = client.get("/").get_data(as_text=True)
    assert "備品を登録" not in html
    assert ">修正<" not in html and ">削除<" not in html
    assert ">貸出<" not in html and ">返却<" not in html


def test_login_failure_message_does_not_reveal_which_is_wrong(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER)
    wrong_password = login(client, MANAGER, "bad-pass").get_data(as_text=True)
    wrong_number = login(client, "9999999").get_data(as_text=True)
    assert "社員番号またはパスワードが違います" in wrong_password
    assert "社員番号またはパスワードが違います" in wrong_number


@pytest.mark.parametrize(
    "method,path,data",
    [
        ("get", "/equipment/new/", None),
        ("post", "/equipment/new/", {"equipment_number": "A-1", "name": "x"}),
        ("get", "/equipment/A-1/edit/", None),
        ("post", "/equipment/A-1/edit/", {"equipment_number": "A-2", "name": "y", "revision": "1"}),
        ("post", "/equipment/A-1/delete/", None),
        ("get", "/equipment/A-1/lend/", None),
        ("post", "/equipment/A-1/lend/", {"borrower_id": "1", "lent_on": "2026-01-01"}),
        ("post", "/equipment/A-1/return/", None),
    ],
)
def test_anonymous_requests_are_refused(tmp_path, method, path, data):
    client = make_client(tmp_path)
    register(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})  # 未ログインなので無視される
    response = getattr(client, method)(path, data=data)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login/")
    html = client.get("/login/").get_data(as_text=True)
    assert "この操作は担当者だけが行えます" in html


def test_employee_requests_are_refused_and_data_unchanged(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER)
    register(client, EMPLOYEE)
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "x"})
    client.post("/logout/")
    login(client, EMPLOYEE)
    response = client.post("/equipment/A-1/delete/")
    assert response.headers["Location"].endswith("/")
    html = client.get("/").get_data(as_text=True)
    assert "この操作は担当者だけが行えます" in html
    assert 'data-equipment-number="A-1"' in html


def test_idle_timeout_logs_out(tmp_path):
    client = make_client(tmp_path, idle_timeout=1)
    register(client, MANAGER, "山田太郎")
    login(client, MANAGER)
    assert "山田太郎" in client.get("/").get_data(as_text=True)
    time.sleep(1.2)
    html = client.get("/").get_data(as_text=True)
    assert "セッションの有効期限が切れました。ログインしてください" in html
    assert "山田太郎" not in html


def test_equipment_crud_as_manager(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER)
    login(client, MANAGER)
    assert client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "旧"}).status_code == 302
    html = client.get("/").get_data(as_text=True)
    assert 'data-equipment-number="A-1"' in html and "旧" in html
    revision = re.search(r'name="revision" value="(\d+)"', client.get("/equipment/A-1/edit/").get_data(as_text=True))
    client.post("/equipment/A-1/edit/", data={"equipment_number": "A-1", "name": "新", "revision": revision.group(1)})
    assert "新" in client.get("/").get_data(as_text=True)
    client.post("/equipment/A-1/delete/")
    assert "備品は登録されていません" in client.get("/").get_data(as_text=True)


def test_form_errors_keep_input(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER)
    login(client, MANAGER)
    html = client.post("/equipment/new/", data={"equipment_number": "PC 1", "name": "残す名前"}).get_data(as_text=True)
    assert "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください" in html
    assert 'value="残す名前"' in html


def test_manager_lends_and_status_shows_borrower_and_date(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    register(client, EMPLOYEE, "佐藤花子")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
    form = client.get("/equipment/A-1/lend/").get_data(as_text=True)
    assert "備品: A-1 ノート" in form
    borrower = borrower_option_value(form, "佐藤花子", EMPLOYEE)
    response = client.post("/equipment/A-1/lend/", data={"borrower_id": borrower, "lent_on": "2026-11-05"})
    assert response.headers["Location"].endswith("/")
    html = client.get("/").get_data(as_text=True)
    assert "貸出を登録しました" in html
    assert "貸出中" in html and "佐藤花子" in html and "2026-11-05" in html
    assert ">返却<" in html and ">貸出<" not in html


def test_lend_validation_errors_are_shown_at_fields(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    register(client, EMPLOYEE, "佐藤花子")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
    html = client.post("/equipment/A-1/lend/", data={"borrower_id": "", "lent_on": "2999-01-01"}).get_data(as_text=True)
    assert "借りる社員を選んでください" in html
    assert "貸出日に未来の日付は入力できません" in html
    assert 'value="2999-01-01"' in html


def test_lending_a_lent_equipment_is_refused_with_message(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    register(client, EMPLOYEE, "佐藤花子")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
    borrower = borrower_option_value(client.get("/equipment/A-1/lend/").get_data(as_text=True), "佐藤花子", EMPLOYEE)
    client.post("/equipment/A-1/lend/", data={"borrower_id": borrower, "lent_on": "2026-11-05"})
    html = client.get("/equipment/A-1/lend/", follow_redirects=True).get_data(as_text=True)
    assert "この備品は既に貸出中です" in html
    html = client.post("/equipment/A-1/lend/", data={"borrower_id": borrower, "lent_on": "2026-11-05"}, follow_redirects=True).get_data(as_text=True)
    assert "この備品は既に貸出中です" in html


def test_return_and_second_return_and_delete_refusal(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    register(client, EMPLOYEE, "佐藤花子")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
    borrower = borrower_option_value(client.get("/equipment/A-1/lend/").get_data(as_text=True), "佐藤花子", EMPLOYEE)
    client.post("/equipment/A-1/lend/", data={"borrower_id": borrower, "lent_on": "2026-11-05"})
    html = client.post("/equipment/A-1/delete/", follow_redirects=True).get_data(as_text=True)
    assert "この備品は貸出中のため削除できません。先に返却を処理してください" in html
    assert 'data-equipment-number="A-1"' in html
    html = client.post("/equipment/A-1/return/", follow_redirects=True).get_data(as_text=True)
    assert "返却を処理しました" in html and "貸出中" not in html
    html = client.post("/equipment/A-1/return/", follow_redirects=True).get_data(as_text=True)
    assert "この備品は既に返却されています" in html


def test_stale_edit_is_refused_with_error_and_keeps_input(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "旧"})
    page = client.get("/equipment/A-1/edit/").get_data(as_text=True)
    revision = re.search(r'name="revision" value="(\d+)"', page).group(1)
    # 別の画面（担当者の別のブラウザ）が先に保存する
    client.post("/equipment/A-1/edit/", data={"equipment_number": "A-1", "name": "先の更新", "revision": revision})
    html = client.post(
        "/equipment/A-1/edit/",
        data={"equipment_number": "A-1", "name": "古い画面の入力", "revision": revision},
    ).get_data(as_text=True)
    assert 'class="error">他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください' in html
    assert 'value="古い画面の入力"' in html


def test_stale_edit_after_delete_is_refused_with_error(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "旧"})
    page = client.get("/equipment/A-1/edit/").get_data(as_text=True)
    revision = re.search(r'name="revision" value="(\d+)"', page).group(1)
    client.post("/equipment/A-1/delete/")
    html = client.post(
        "/equipment/A-1/edit/",
        data={"equipment_number": "A-1", "name": "新", "revision": revision},
    ).get_data(as_text=True)
    assert "他の担当者が先にこの備品を更新しました" in html


def test_edit_keeps_lending_record(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    register(client, EMPLOYEE, "佐藤花子")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "旧"})
    borrower = borrower_option_value(client.get("/equipment/A-1/lend/").get_data(as_text=True), "佐藤花子", EMPLOYEE)
    client.post("/equipment/A-1/lend/", data={"borrower_id": borrower, "lent_on": "2026-11-05"})
    page = client.get("/equipment/A-1/edit/").get_data(as_text=True)
    revision = re.search(r'name="revision" value="(\d+)"', page).group(1)
    client.post("/equipment/A-1/edit/", data={"equipment_number": "A-2", "name": "新", "revision": revision})
    html = client.get("/").get_data(as_text=True)
    assert 'data-equipment-number="A-2"' in html and "佐藤花子" in html and "2026-11-05" in html


def test_employee_and_anonymous_cannot_lend_or_return(tmp_path):
    client = make_client(tmp_path)
    register(client, MANAGER, "山田太郎")
    register(client, EMPLOYEE, "佐藤花子")
    login(client, MANAGER)
    client.post("/equipment/new/", data={"equipment_number": "A-1", "name": "ノート"})
    client.post("/logout/")
    login(client, EMPLOYEE)
    html = client.get("/").get_data(as_text=True)
    assert ">貸出<" not in html and ">返却<" not in html
    response = client.get("/equipment/A-1/lend/")
    assert response.headers["Location"].endswith("/")
    assert "この操作は担当者だけが行えます" in client.get("/").get_data(as_text=True)

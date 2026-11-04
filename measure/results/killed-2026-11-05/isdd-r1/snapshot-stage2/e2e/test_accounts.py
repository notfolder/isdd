"""アカウント登録・ログイン・無操作の自動ログアウトの E2E。"""

from support import login, logout, register


def test_register_account(start_app, page):
    """最初の登録は担当者、次は社員。形式違いと重複は文言どおり。"""
    app = start_app()
    base = app.base_url

    register(page, base, "1234567", "山田太郎")
    assert page.url.endswith("/login/")
    assert page.locator(".message").inner_text() == "登録しました。ログインしてください"

    register(page, base, "2345678", "佐藤花子")
    assert page.url.endswith("/login/")

    # 担当者（最初の登録者）はログインすると「備品を登録」が見える
    login(page, base, "1234567")
    assert page.get_by_role("link", name="備品を登録").count() == 1
    logout(page)

    # 社員（2 件目）には「備品を登録」が出ない
    login(page, base, "2345678")
    assert page.get_by_role("link", name="備品を登録").count() == 0
    logout(page)

    # 形式違い（6 桁）
    register(page, base, "123456", "名前")
    field = page.locator(".field", has=page.locator("#id_employee_number"))
    assert field.locator(".field-error").inner_text() == "社員番号は 7 桁の数字で入力してください"
    assert page.input_value("#id_name") == "名前"

    # 重複
    register(page, base, "1234567", "別人")
    field = page.locator(".field", has=page.locator("#id_employee_number"))
    assert field.locator(".field-error").inner_text() == "この社員番号は既に登録されています"

    # 名前が空と、パスワードが短い
    register(page, base, "3456789", "", password="short")
    assert page.locator(".field", has=page.locator("#id_name")).locator(".field-error").inner_text() == "名前を入力してください"
    assert page.locator(".field", has=page.locator("#id_password")).locator(".field-error").inner_text() == "パスワードは 8 文字以上で入力してください"


def test_login_logout(start_app, page):
    """失敗時はどちらが違うかを示さず、成功で名前を出し、ログアウトで戻る。"""
    app = start_app()
    base = app.base_url
    register(page, base, "1234567", "山田太郎")

    login(page, base, "1234567", password="wrong-pass")
    assert page.locator(".error").inner_text() == "社員番号またはパスワードが違います"

    login(page, base, "9999999")
    assert page.locator(".error").inner_text() == "社員番号またはパスワードが違います"

    login(page, base, "1234567")
    assert page.locator(".current-user").inner_text() == "山田太郎"

    logout(page)
    assert page.locator(".current-user").count() == 0
    assert page.get_by_role("link", name="ログイン").count() == 1


def test_idle_logout(start_app, page):
    """無操作の期限（2 秒）を過ぎると自動でログアウトする。"""
    app = start_app(idle_timeout=2)
    base = app.base_url
    register(page, base, "1234567", "山田太郎")
    login(page, base, "1234567")
    assert page.locator(".current-user").inner_text() == "山田太郎"

    page.wait_for_timeout(3000)
    page.goto(base + "/")
    assert page.locator(".current-user").count() == 0
    assert page.locator(".message").inner_text() == "セッションの有効期限が切れました。ログインしてください"

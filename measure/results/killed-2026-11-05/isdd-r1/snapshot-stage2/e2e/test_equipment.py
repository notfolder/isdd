"""備品の一覧・登録・修正・削除、担当者以外の操作の拒否の E2E。"""

from support import create_equipment, login, logout, register, row


def test_view_status(start_app, page):
    """未ログインでも一覧を見られる。0 件の文言、管理番号の昇順、全件空き、ボタン無し。"""
    app = start_app()
    base = app.base_url
    page.goto(base + "/")
    assert page.locator("p.empty").inner_text() == "備品は登録されていません"
    assert page.locator("tbody tr").count() == 0

    register(page, base, "1234567", "山田太郎")
    login(page, base, "1234567")
    for number, name in [("B-002", "プロジェクター"), ("A-001", "ノートパソコン"), ("C-010", "延長コード")]:
        create_equipment(page, base, number, name)
    logout(page)

    page.goto(base + "/")
    numbers = page.locator("tbody tr").evaluate_all("rows => rows.map(r => r.dataset.equipmentNumber)")
    assert numbers == ["A-001", "B-002", "C-010"]
    statuses = page.locator("tbody tr td:nth-child(3)").all_inner_texts()
    assert statuses == ["空き", "空き", "空き"]
    assert page.get_by_role("button", name="修正").count() == 0
    assert page.get_by_role("button", name="削除").count() == 0


def test_create_equipment(start_app, page):
    """担当者が登録できる。形式違い・重複・長い名前は文言どおり。"""
    app = start_app()
    base = app.base_url
    register(page, base, "1234567", "山田太郎")
    login(page, base, "1234567")

    create_equipment(page, base, "PC-0001", "ノートパソコン")
    assert page.locator(".message").inner_text() == "備品を登録しました"
    assert row(page, "PC-0001").count() == 1

    create_equipment(page, base, "PC 001", "形式違い")
    field = page.locator(".field", has=page.locator("#id_equipment_number"))
    assert field.locator(".field-error").inner_text() == "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    assert page.input_value("#id_name") == "形式違い"

    create_equipment(page, base, "PC-0001", "重複")
    field = page.locator(".field", has=page.locator("#id_equipment_number"))
    assert field.locator(".field-error").inner_text() == "この管理番号は既に使われています"
    assert page.input_value("#id_equipment_number") == "PC-0001"

    create_equipment(page, base, "PC-0002", "a" * 51)
    field = page.locator(".field", has=page.locator("#id_name"))
    assert field.locator(".field-error").inner_text() == "備品名は 50 文字以内で入力してください"


def test_update_equipment(start_app, page):
    """担当者が修正できる。重なる管理番号は拒否される。"""
    app = start_app()
    base = app.base_url
    register(page, base, "1234567", "山田太郎")
    login(page, base, "1234567")
    create_equipment(page, base, "A-001", "旧名")
    create_equipment(page, base, "B-002", "別の備品")

    row(page, "A-001").get_by_role("button", name="修正").click()
    page.fill("#id_name", "新名")
    page.get_by_role("button", name="保存").click()
    assert page.locator(".message").inner_text() == "備品を修正しました"
    assert row(page, "A-001").locator("td").nth(1).inner_text() == "新名"

    row(page, "B-002").get_by_role("button", name="修正").click()
    page.fill("#id_equipment_number", "A-001")
    page.get_by_role("button", name="保存").click()
    field = page.locator(".field", has=page.locator("#id_equipment_number"))
    assert field.locator(".field-error").inner_text() == "この管理番号は既に使われています"


def test_delete_equipment(start_app, page):
    """確認ダイアログで「キャンセル」なら残り、「はい」なら消える。"""
    app = start_app()
    base = app.base_url
    register(page, base, "1234567", "山田太郎")
    login(page, base, "1234567")
    create_equipment(page, base, "D-001", "削除対象")

    dialogs = []

    def dismiss(dialog):
        dialogs.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss)
    row(page, "D-001").get_by_role("button", name="削除").click()
    page.wait_for_timeout(300)
    assert dialogs and "よろしいですか" in dialogs[0]
    assert row(page, "D-001").count() == 1

    page.once("dialog", lambda dialog: dialog.accept())
    row(page, "D-001").get_by_role("button", name="削除").click()
    assert page.locator(".message").inner_text() == "備品を削除しました"
    assert row(page, "D-001").count() == 0


def test_restrict_non_manager(start_app, page):
    """社員と未ログインは、ボタンが出ず、直接の要求も拒否される。"""
    app = start_app()
    base = app.base_url
    register(page, base, "1234567", "山田太郎")
    register(page, base, "2345678", "佐藤花子")
    login(page, base, "1234567")
    create_equipment(page, base, "E-001", "テスト備品")
    logout(page)

    # 社員: 一覧にボタンも「備品を登録」も無い。直接の要求は拒否される
    login(page, base, "2345678")
    page.goto(base + "/")
    assert page.get_by_role("button", name="修正").count() == 0
    assert page.get_by_role("button", name="削除").count() == 0
    assert page.get_by_role("link", name="備品を登録").count() == 0
    response = page.request.post(base + "/equipment/E-001/delete/")
    assert "この操作は担当者だけが行えます" in response.text()
    response = page.request.get(base + "/equipment/new/")
    assert "この操作は担当者だけが行えます" in response.text()
    logout(page)

    # 未ログイン: 登録・修正・削除の要求は拒否され、ログイン画面へ戻る
    page.context.clear_cookies()
    response = page.request.post(base + "/equipment/E-001/edit/", form={"equipment_number": "X-1", "name": "改ざん"})
    assert "この操作は担当者だけが行えます" in response.text()
    response = page.request.post(base + "/equipment/E-001/delete/")
    assert "この操作は担当者だけが行えます" in response.text()

    # 備品は変わっていない
    page.goto(base + "/")
    assert row(page, "E-001").locator("td").nth(1).inner_text() == "テスト備品"
    assert row(page, "X-1").count() == 0

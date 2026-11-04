"""貸出・返却、貸出中の削除の拒否、修正の競合、貸出状況の表示、社員と未ログインの制限の E2E。

同じ担当者アカウントを 2 つのブラウザで使い、2 人の担当者の同時の操作を再現する。
"""

from support import create_equipment, login, lend, logout, new_manager_page, register, row, today_jst

MANAGER = "1234567"
EMPLOYEE = "2345678"
EMPLOYEE_LABEL = "佐藤花子（2345678）"


def setup_manager_and_employee(page, base):
    register(page, base, MANAGER, "山田太郎")
    register(page, base, EMPLOYEE, "佐藤花子")
    login(page, base, MANAGER)


def test_lend_equipment(start_app, page):
    """担当者が空きの備品を貸し出す。借りる社員の未選択と未来の貸出日は文言どおり出る。"""
    app = start_app()
    base = app.base_url
    setup_manager_and_employee(page, base)
    create_equipment(page, base, "A-001", "ノート")

    row(page, "A-001").get_by_role("button", name="貸出").click()
    assert page.locator(".lending-equipment").inner_text() == "備品: A-001 ノート"
    assert page.input_value("#id_lent_on") == today_jst()

    page.fill("#id_lent_on", "2999-01-01")
    page.get_by_role("button", name="登録").click()
    field = page.locator(".field", has=page.locator("#id_borrower"))
    assert field.locator(".field-error").inner_text() == "借りる社員を選んでください"
    field = page.locator(".field", has=page.locator("#id_lent_on"))
    assert field.locator(".field-error").inner_text() == "貸出日に未来の日付は入力できません"
    assert page.input_value("#id_lent_on") == "2999-01-01"

    page.select_option("#id_borrower", label=EMPLOYEE_LABEL)
    page.fill("#id_lent_on", today_jst())
    page.get_by_role("button", name="登録").click()
    assert page.locator(".message").inner_text() == "貸出を登録しました"
    cells = row(page, "A-001").locator("td").all_inner_texts()
    assert cells[2] == "貸出中"
    assert cells[3] == "佐藤花子"
    assert cells[4] == today_jst()


def test_prevent_double_lending(start_app, page):
    """2 つのブラウザで同じ空きの備品を同時に開いて貸し出すと、先の登録だけが記録される。"""
    app = start_app()
    base = app.base_url
    setup_manager_and_employee(page, base)
    create_equipment(page, base, "B-001", "プロジェクター")

    other, context = new_manager_page(page)
    try:
        login(other, base, MANAGER)
        other.goto(base + "/equipment/B-001/lend/")  # 登録前に開いたままにする

        lend(page, base, "B-001", EMPLOYEE_LABEL, today_jst())
        assert page.locator(".message").inner_text() == "貸出を登録しました"

        other.select_option("#id_borrower", label=EMPLOYEE_LABEL)
        other.get_by_role("button", name="登録").click()
        assert other.locator(".message").inner_text() == "この備品は既に貸出中です"
        assert row(other, "B-001").locator("td").nth(2).inner_text() == "貸出中"
    finally:
        context.close()


def test_return_equipment(start_app, page):
    """返却は確認で「はい」のときだけ行われ、空きに戻る。二重の返却は「既に返却されています」。"""
    app = start_app()
    base = app.base_url
    setup_manager_and_employee(page, base)
    create_equipment(page, base, "C-001", "延長コード")
    lend(page, base, "C-001", EMPLOYEE_LABEL, today_jst())

    other, context = new_manager_page(page)
    try:
        login(other, base, MANAGER)
        other.goto(base + "/")  # 貸出中の画面を開いたままにする

        page.goto(base + "/")
        page.once("dialog", lambda dialog: dialog.dismiss())
        row(page, "C-001").get_by_role("button", name="返却").click()
        page.wait_for_timeout(300)
        assert row(page, "C-001").locator("td").nth(2).inner_text() == "貸出中"

        page.once("dialog", lambda dialog: dialog.accept())
        row(page, "C-001").get_by_role("button", name="返却").click()
        assert page.locator(".message").inner_text() == "返却を処理しました"
        cells = row(page, "C-001").locator("td").all_inner_texts()
        assert cells[2] == "空き" and cells[3] == "" and cells[4] == ""

        other.once("dialog", lambda dialog: dialog.accept())
        row(other, "C-001").get_by_role("button", name="返却").click()
        assert other.locator(".message").inner_text() == "この備品は既に返却されています"
    finally:
        context.close()


def test_refuse_delete_lent_equipment(start_app, page):
    """貸出中の備品は、確認で「はい」を選んでも削除されない。"""
    app = start_app()
    base = app.base_url
    setup_manager_and_employee(page, base)
    create_equipment(page, base, "D-001", "貸出中の備品")
    lend(page, base, "D-001", EMPLOYEE_LABEL, today_jst())

    page.goto(base + "/")
    page.once("dialog", lambda dialog: dialog.accept())
    row(page, "D-001").get_by_role("button", name="削除").click()
    assert page.locator(".message").inner_text() == "この備品は貸出中のため削除できません。先に返却を処理してください"
    assert row(page, "D-001").count() == 1
    assert row(page, "D-001").locator("td").nth(2).inner_text() == "貸出中"


def test_update_equipment_conflict(start_app, page):
    """開いてから他の担当者が更新・削除したら、保存は拒否され開き直すよう出る。貸出の記録は残る。"""
    app = start_app()
    base = app.base_url
    setup_manager_and_employee(page, base)
    create_equipment(page, base, "E-001", "旧名")
    create_equipment(page, base, "E-002", "削除される備品")
    lend(page, base, "E-001", EMPLOYEE_LABEL, today_jst())

    other, context = new_manager_page(page)
    try:
        login(other, base, MANAGER)

        # 別の担当者が先に修正する
        page.goto(base + "/")
        row(page, "E-001").get_by_role("button", name="修正").click()  # 開いたまま
        other.goto(base + "/")
        row(other, "E-001").get_by_role("button", name="修正").click()
        other.fill("#id_name", "先の更新")
        other.get_by_role("button", name="保存").click()
        assert other.locator(".message").inner_text() == "備品を修正しました"

        page.fill("#id_name", "古い画面の入力")
        page.get_by_role("button", name="保存").click()
        assert page.locator(".error").inner_text() == (
            "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
        )
        assert page.input_value("#id_name") == "古い画面の入力"

        # 開き直してから保存すると、直した内容と貸出の記録が残る
        page.goto(base + "/")
        row(page, "E-001").get_by_role("button", name="修正").click()
        assert page.input_value("#id_name") == "先の更新"
        page.fill("#id_name", "最新の名前")
        page.get_by_role("button", name="保存").click()
        assert page.locator(".message").inner_text() == "備品を修正しました"
        cells = row(page, "E-001").locator("td").all_inner_texts()
        assert cells[1] == "最新の名前" and cells[2] == "貸出中" and cells[3] == "佐藤花子"

        # 別の担当者が先に削除した備品の保存も拒否される
        page.goto(base + "/")
        row(page, "E-002").get_by_role("button", name="修正").click()
        other.goto(base + "/")
        other.once("dialog", lambda dialog: dialog.accept())
        row(other, "E-002").get_by_role("button", name="削除").click()
        assert other.locator(".message").inner_text() == "備品を削除しました"
        page.fill("#id_name", "削除後の保存")
        page.get_by_role("button", name="保存").click()
        assert page.locator(".error").inner_text() == (
            "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
        )
    finally:
        context.close()


def test_restrict_lending_non_manager(start_app, page):
    """社員と未ログインは、貸出・返却のボタンが出ず、直接の要求も拒否される。"""
    app = start_app()
    base = app.base_url
    setup_manager_and_employee(page, base)
    create_equipment(page, base, "F-001", "空きの備品")
    create_equipment(page, base, "F-002", "貸出中の備品")
    lend(page, base, "F-002", EMPLOYEE_LABEL, today_jst())
    logout(page)

    login(page, base, EMPLOYEE)
    page.goto(base + "/")
    assert page.get_by_role("button", name="貸出").count() == 0
    assert page.get_by_role("button", name="返却").count() == 0
    response = page.request.get(base + "/equipment/F-001/lend/")
    assert "この操作は担当者だけが行えます" in response.text()
    response = page.request.post(base + "/equipment/F-002/return/")
    assert "この操作は担当者だけが行えます" in response.text()
    logout(page)

    page.context.clear_cookies()
    response = page.request.post(base + "/equipment/F-002/return/")
    assert "この操作は担当者だけが行えます" in response.text()

    page.goto(base + "/")
    cells = row(page, "F-002").locator("td").all_inner_texts()
    assert cells[2] == "貸出中" and cells[3] == "佐藤花子"


def test_view_lending_status(start_app, page):
    """貸出状況の一覧に、貸出中、借りている社員の名前、貸出日が出る。未ログインにボタンは無い。"""
    app = start_app()
    base = app.base_url
    setup_manager_and_employee(page, base)
    create_equipment(page, base, "H-001", "ノート")
    create_equipment(page, base, "H-002", "プロジェクター")
    lend(page, base, "H-002", EMPLOYEE_LABEL, "2026-11-01")
    logout(page)

    page.goto(base + "/")
    free = row(page, "H-001").locator("td").all_inner_texts()
    assert free[2] == "空き" and free[3] == "" and free[4] == ""
    lent = row(page, "H-002").locator("td").all_inner_texts()
    assert lent[2] == "貸出中" and lent[3] == "佐藤花子" and lent[4] == "2026-11-01"
    assert page.get_by_role("button", name="貸出").count() == 0
    assert page.get_by_role("button", name="返却").count() == 0

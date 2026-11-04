"""セッション期限の判定の結合テスト。"""

from app import accounts


def _login(app, client):
    with app.app_context():
        account_id, _ = accounts.register_account("000001", "担当", "password1")
    client.post("/login/", data={"employee_number": "000001", "password": "password1"})
    return account_id


def test_session_stays_valid_within_timeout(app, client):
    _login(app, client)
    response = client.get("/equipment/new/")
    assert response.status_code == 200


def test_session_expires_after_timeout(make_app):
    app = make_app(idle_timeout=-1)  # 既に期限切れとして扱う
    client = app.test_client()
    with app.app_context():
        accounts.register_account("000001", "担当", "password1")
    client.post("/login/", data={"employee_number": "000001", "password": "password1"})
    response = client.get("/equipment/new/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login/")

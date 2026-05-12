"""
予約機能と部署表示機能のバックエンドAPIテスト。

要件トレーサビリティ:
  要件ID: RQ-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
  設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
  要件概要: 返却予定日付き貸出、予約遷移、重複拒否、返却時削除を検証する。
  設計概要: TestClientで予約系APIと一覧APIを呼び出し、正常系/異常系の応答を確認する。
  呼び出し先設計ID: DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION, DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE, DS-FN-DELETE-LOANED-RESERVATION-ON-RETURN-FT-DELETE-LOANED-RESERVATION-ON-RETURN, DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT
  呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from fastapi.testclient import TestClient


def _load_app_module():
    """
    backend/app/main.py を動的ロードしてモジュールを返す。

    Returns:
      backendアプリモジュール。

    要件トレーサビリティ:
      要件ID: RQ-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
      設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
      要件概要: テスト実行時のモジュール解決を安定化する。
      設計概要: ファイルパス指定でFastAPIモジュールを明示的に読み込む。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    module_path = Path(__file__).resolve().parents[1] / "app" / "main.py"
    spec = importlib.util.spec_from_file_location("backend_app_main", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("backend appモジュールの読み込みに失敗しました")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_client() -> TestClient:
    """
    テスト用FastAPIクライアントを生成する。

    Returns:
      初期化済みTestClient。

    要件トレーサビリティ:
      要件ID: RQ-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
      設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
      要件概要: テスト環境で予約関連APIを実行できること。
      設計概要: backend/app/main.py を読み込み、起動イベントでDBを初期化する。
      呼び出し先設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    os.environ["EXTERNAL_DEPARTMENT_DB_USE_MOCK"] = "1"
    app_main = _load_app_module()

    # テスト前に永続DBをクリーンアップして再現性を確保する。
    db_path = Path(app_main.DB_PATH)
    if db_path.exists():
        db_path.unlink()
    app_main.SESSIONS.clear()
    app_main.initialize_database()

    return TestClient(app_main.app)


def _login(client: TestClient, login_id: str, password: str) -> dict[str, str]:
    """
    ログインして認証ヘッダーを返す。

    Args:
      client: TestClient。
      login_id: ログインID。
      password: パスワード。

    Returns:
      Authorizationヘッダー辞書。

    要件トレーサビリティ:
      要件ID: RQ-FT-AUTHENTICATE-USER
      設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      要件概要: 認証済みユーザーのみAPIを利用できる。
      設計概要: 認証API応答のトークンをBearer形式で返す。
      呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    response = client.post(
        "/api/auth/login",
        json={"login_id": login_id, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _create_user(
    client: TestClient,
    headers: dict[str, str],
    login_id: str,
    display_name: str,
    initial_password: str,
) -> None:
    """
    テスト用ユーザーを作成する。

    Args:
      client: TestClient。
      headers: 管理者ヘッダー。
      login_id: ログインID。
      display_name: 表示名。
      initial_password: 初期パスワード。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-USER
      設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
      要件概要: 管理者がユーザーを登録できる。
      設計概要: APIでユーザー登録を実行する。
      呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    response = client.post(
        "/api/users",
        headers=headers,
        json={
            "login_id": login_id,
            "display_name": display_name,
            "role": "一般ユーザー",
            "initial_password": initial_password,
        },
    )
    assert response.status_code == 200


def _create_asset(client: TestClient, headers: dict[str, str], asset_number: str) -> None:
    """
    テスト用備品を作成する。

    Args:
      client: TestClient。
      headers: 管理者ヘッダー。
      asset_number: 資産管理番号。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-ASSET
      設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
      要件概要: 管理者が備品を登録できる。
      設計概要: APIで備品登録を実行する。
      呼び出し先設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    response = client.post(
        "/api/assets",
        headers=headers,
        json={"asset_number": asset_number, "asset_name": f"{asset_number}-name"},
    )
    assert response.status_code == 200


def test_reservation_overlap_rejected() -> None:
    """
    予約重複が拒否されることを確認する。

    要件トレーサビリティ:
      要件ID: RQ-TS-REJECT-RESERVATION-WITH-OVERLAP
      設計ID: DS-MD-REJECT-RESERVATION-WITH-OVERLAP-TS-REJECT-RESERVATION-WITH-OVERLAP
      要件概要: 同一備品の期間重複予約を拒否する。
      設計概要: 先行予約を作成後、境界重複する予約登録が409になることを確認する。
      呼び出し先設計ID: DS-FN-VALIDATE-RESERVATION-PERIOD-OVERLAP-FT-VALIDATE-RESERVATION-PERIOD-OVERLAP
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    client = _create_client()
    admin_headers = _login(client, "admin", "admin")
    _create_user(client, admin_headers, "U001", "予約者1", "U001")
    _create_asset(client, admin_headers, "A-RES-001")

    user_headers = _login(client, "U001", "U001")
    first_response = client.post(
        "/api/assets/A-RES-001/reservations",
        headers=user_headers,
        json={
            "reserver_login_id": "U001",
            "start_date": "2030-05-10",
            "end_date": "2030-05-12",
        },
    )
    assert first_response.status_code == 200

    overlap_response = client.post(
        "/api/assets/A-RES-001/reservations",
        headers=user_headers,
        json={
            "reserver_login_id": "U001",
            "start_date": "2030-05-12",
            "end_date": "2030-05-14",
        },
    )
    assert overlap_response.status_code == 409


def test_loan_moves_reservation_to_loaned_and_return_deletes() -> None:
    """
    貸出で予約が貸出済みに遷移し、返却で削除されることを確認する。

    要件トレーサビリティ:
      要件ID: RQ-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
      設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
      要件概要: 返却予定日付き貸出時に予約遷移し、返却時に貸出済み予約が削除される。
      設計概要: 予約作成後に貸出・返却APIを順次呼び出し、予約一覧件数を検証する。
      呼び出し先設計ID: DS-FN-TRANSITION-RESERVATION-TO-LOANED-FT-TRANSITION-RESERVATION-TO-LOANED, DS-FN-DELETE-LOANED-RESERVATION-ON-RETURN-FT-DELETE-LOANED-RESERVATION-ON-RETURN
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    client = _create_client()
    admin_headers = _login(client, "admin", "admin")
    _create_user(client, admin_headers, "U002", "予約者2", "U002")
    _create_asset(client, admin_headers, "A-RES-002")

    user_headers = _login(client, "U002", "U002")
    reservation_response = client.post(
        "/api/assets/A-RES-002/reservations",
        headers=user_headers,
        json={
            "reserver_login_id": "U002",
            "start_date": "2030-06-01",
            "end_date": "2030-06-05",
        },
    )
    assert reservation_response.status_code == 200

    loan_response = client.post(
        "/api/assets/A-RES-002/loan",
        headers=admin_headers,
        json={
            "borrower_login_id": "U002",
            "loan_date": "2030-06-01",
            "return_due_date": "2030-06-05",
        },
    )
    assert loan_response.status_code == 200

    reserved_items_response = client.get(
        "/api/assets/A-RES-002/reservations?year_month=2030-06",
        headers=admin_headers,
    )
    assert reserved_items_response.status_code == 200
    items = reserved_items_response.json()["items"]
    assert len(items) == 1
    assert items[0]["reservation_status"] == "貸出済み"

    return_response = client.post("/api/assets/A-RES-002/return", headers=admin_headers)
    assert return_response.status_code == 200

    after_return_response = client.get(
        "/api/assets/A-RES-002/reservations?year_month=2030-06",
        headers=admin_headers,
    )
    assert after_return_response.status_code == 200
    assert after_return_response.json()["items"] == []


def test_reservation_rejected_when_return_due_date_missing() -> None:
    """
    返却予定日未設定の貸出中備品への予約が拒否されることを確認する。

    要件トレーサビリティ:
      要件ID: RQ-TS-REJECT-RESERVATION-WHEN-RETURN-DUE-DATE-MISSING
      設計ID: DS-MD-REJECT-RESERVATION-WHEN-RETURN-DUE-DATE-MISSING-TS-REJECT-RESERVATION-WHEN-RETURN-DUE-DATE-MISSING
      要件概要: 返却予定日未設定の場合に予約受付を拒否する。
      設計概要: DBを直接更新して欠落状態を作り、予約APIが409を返すことを確認する。
      呼び出し先設計ID: DS-FN-REJECT-RESERVATION-WHEN-RETURN-DUE-DATE-MISSING-FT-REJECT-RESERVATION-WHEN-RETURN-DUE-DATE-MISSING
      呼び出し元設計ID: DS-MD-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION-TS-VERIFY-LOAN-WITH-RETURN-DUE-DATE-AND-RESERVATION
    """

    client = _create_client()
    admin_headers = _login(client, "admin", "admin")
    _create_user(client, admin_headers, "U003", "予約者3", "U003")
    _create_asset(client, admin_headers, "A-RES-003")

    loan_response = client.post(
        "/api/assets/A-RES-003/loan",
        headers=admin_headers,
        json={
            "borrower_login_id": "U003",
            "loan_date": "2030-07-01",
            "return_due_date": "2030-07-03",
        },
    )
    assert loan_response.status_code == 200

    app_main = _load_app_module()
    db_path = Path(app_main.DB_PATH)
    import sqlite3

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE asset_master SET return_due_date = NULL WHERE asset_number = ?",
            ("A-RES-003",),
        )
        connection.commit()

    user_headers = _login(client, "U003", "U003")
    reservation_response = client.post(
        "/api/assets/A-RES-003/reservations",
        headers=user_headers,
        json={
            "reserver_login_id": "U003",
            "start_date": "2030-07-02",
            "end_date": "2030-07-04",
        },
    )
    assert reservation_response.status_code == 409


def test_department_name_visible_in_asset_and_reservation_views() -> None:
    """
    備品一覧と予約一覧で部署名が表示されることを確認する。

    要件トレーサビリティ:
      要件ID: RQ-TS-VERIFY-DEPARTMENT-NAME-ASYNC-DISPLAY
      設計ID: DS-MD-VERIFY-DEPARTMENT-NAME-ASYNC-DISPLAY-TS-VERIFY-DEPARTMENT-NAME-ASYNC-DISPLAY
      要件概要: 部署名を一覧と予約画面で確認できる。
      設計概要: U001(営業部)を使って一覧APIと予約一覧APIの部署表示値を検証する。
      呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
      呼び出し元設計ID: DS-MD-VERIFY-DEPARTMENT-NAME-ASYNC-DISPLAY-TS-VERIFY-DEPARTMENT-NAME-ASYNC-DISPLAY
    """

    client = _create_client()
    admin_headers = _login(client, "admin", "admin")
    _create_user(client, admin_headers, "U001", "予約者4", "U001")
    _create_asset(client, admin_headers, "A-RES-004")

    loan_response = client.post(
        "/api/assets/A-RES-004/loan",
        headers=admin_headers,
        json={
            "borrower_login_id": "U001",
            "loan_date": "2030-08-01",
            "return_due_date": "2030-08-02",
        },
    )
    assert loan_response.status_code == 200

    assets_response = client.get("/api/assets", headers=admin_headers)
    assert assets_response.status_code == 200
    target_item = next(
        item for item in assets_response.json()["items"] if item["asset_number"] == "A-RES-004"
    )
    assert target_item["borrower_department_display_status"] == "部署名"
    assert target_item["borrower_department_name"] == "営業部"

    return_response = client.post("/api/assets/A-RES-004/return", headers=admin_headers)
    assert return_response.status_code == 200

    user_headers = _login(client, "U001", "U001")
    register_response = client.post(
        "/api/assets/A-RES-004/reservations",
        headers=user_headers,
        json={
            "reserver_login_id": "U001",
            "start_date": "2030-08-10",
            "end_date": "2030-08-11",
        },
    )
    assert register_response.status_code == 200

    reservations_response = client.get(
        "/api/assets/A-RES-004/reservations?year_month=2030-08",
        headers=admin_headers,
    )
    assert reservations_response.status_code == 200
    reservations = reservations_response.json()["items"]
    assert len(reservations) == 1
    assert reservations[0]["reserver_department_display_status"] == "部署名"
    assert reservations[0]["reserver_department_name"] == "営業部"

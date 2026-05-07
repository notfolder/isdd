"""
予約API 結合テスト（FastAPI TestClient）。

要件トレーサビリティ:
  要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-FT-VIEW-RESERVATION-CALENDAR
  設計ID: DS-FN-TEST-API-RESERVATION-CRUD-FT-MAKE-RESERVATION
  要件概要: 予約CRUD API の正常系・異常系（409重複・403権限・404不存在・401未認証）を検証する。
  設計概要: FastAPI TestClient でエンドポイントを呼び出し、レスポンスコードとボディを検証する。
  呼び出し先: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
  呼び出し元: pytest
"""
import os
import pytest
from sqlalchemy.orm import Session
from app.models.equipment import Equipment
from app.models.user import User


def _setup_equipment(db: Session, equipment_id: str = "EQ-TEST-001"):
    eq = Equipment(equipment_id=equipment_id, name="テスト備品", status="available")
    db.add(eq)
    db.commit()
    return eq


def _setup_user(db: Session, login_id: str = "general01", role: str = "general"):
    import bcrypt
    pw_hash = bcrypt.hashpw("testpass".encode(), bcrypt.gensalt()).decode()
    u = User(login_id=login_id, display_name="一般利用者", password_hash=pw_hash, role=role)
    db.add(u)
    db.commit()
    return u


def _login(client, login_id: str, password: str):
    client.post("/api/auth/login", json={"login_id": login_id, "password": password})


class TestReservationList:
    """GET /api/equipment/{id}/reservations のテスト。"""

    def test_list_returns_empty_for_no_reservations(self, admin_client, db):
        _setup_equipment(db)
        res = admin_client.get("/api/equipment/EQ-TEST-001/reservations")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_requires_login(self, client):
        res = client.get("/api/equipment/EQ-TEST-001/reservations")
        assert res.status_code == 401


class TestReservationCreate:
    """POST /api/equipment/{id}/reservations のテスト。"""

    def test_create_succeeds(self, admin_client, db):
        _setup_equipment(db)
        res = admin_client.post(
            "/api/equipment/EQ-TEST-001/reservations",
            json={"start_date": "2026-07-01", "end_date": "2026-07-05"},
        )
        assert res.status_code == 201
        body = res.json()
        assert body["equipment_id"] == "EQ-TEST-001"
        assert body["start_date"] == "2026-07-01"
        assert body["end_date"] == "2026-07-05"

    def test_create_conflict_returns_409(self, admin_client, db):
        _setup_equipment(db)
        admin_client.post(
            "/api/equipment/EQ-TEST-001/reservations",
            json={"start_date": "2026-07-01", "end_date": "2026-07-05"},
        )
        res = admin_client.post(
            "/api/equipment/EQ-TEST-001/reservations",
            json={"start_date": "2026-07-03", "end_date": "2026-07-08"},
        )
        assert res.status_code == 409
        assert "既に予約されています" in res.json()["detail"]

    def test_create_requires_login(self, client):
        res = client.post(
            "/api/equipment/EQ-TEST-001/reservations",
            json={"start_date": "2026-07-01", "end_date": "2026-07-05"},
        )
        assert res.status_code == 401

    def test_general_user_cannot_reserve_for_others(self, client, db):
        _setup_equipment(db)
        _setup_user(db, "general01", "general")
        _setup_user(db, "other01", "general")
        _login(client, "general01", "testpass")
        res = client.post(
            "/api/equipment/EQ-TEST-001/reservations",
            json={"start_date": "2026-07-01", "end_date": "2026-07-05", "user_login_id": "other01"},
        )
        assert res.status_code == 403

    def test_general_user_can_reserve_for_self(self, client, db):
        _setup_equipment(db)
        _setup_user(db, "general01", "general")
        _login(client, "general01", "testpass")
        res = client.post(
            "/api/equipment/EQ-TEST-001/reservations",
            json={"start_date": "2026-07-01", "end_date": "2026-07-05"},
        )
        assert res.status_code == 201

    def test_create_equipment_not_found_returns_404(self, admin_client):
        res = admin_client.post(
            "/api/equipment/NOT-EXIST/reservations",
            json={"start_date": "2026-07-01", "end_date": "2026-07-05"},
        )
        assert res.status_code == 404


class TestReservationCancel:
    """DELETE /api/reservations/{id} のテスト。"""

    def _create_reservation(self, admin_client, equipment_id="EQ-TEST-001"):
        res = admin_client.post(
            f"/api/equipment/{equipment_id}/reservations",
            json={"start_date": "2026-08-01", "end_date": "2026-08-05"},
        )
        return res.json()["reservation_id"]

    def test_admin_can_cancel(self, admin_client, db):
        _setup_equipment(db)
        reservation_id = self._create_reservation(admin_client)
        res = admin_client.delete(f"/api/reservations/{reservation_id}")
        assert res.status_code == 204

    def test_cancel_not_found_returns_404(self, admin_client):
        res = admin_client.delete("/api/reservations/non-existent-id")
        assert res.status_code == 404

    def test_other_user_cannot_cancel(self, client, db):
        _setup_equipment(db)
        _setup_user(db, "user-a", "general")
        _setup_user(db, "user-b", "general")
        _login(client, "user-a", "testpass")
        res = client.post(
            "/api/equipment/EQ-TEST-001/reservations",
            json={"start_date": "2026-09-01", "end_date": "2026-09-05"},
        )
        reservation_id = res.json()["reservation_id"]
        _login(client, "user-b", "testpass")
        res2 = client.delete(f"/api/reservations/{reservation_id}")
        assert res2.status_code == 403

    def test_cancel_requires_login(self, client):
        res = client.delete("/api/reservations/some-id")
        assert res.status_code == 401


class TestDepartmentApi:
    """GET /api/department/by-login-id のテスト。"""

    def test_returns_unknown_for_unknown_user(self, admin_client):
        res = admin_client.get("/api/department/by-login-id?login_id=nonexistent")
        assert res.status_code == 200
        assert res.json()["department_name"] == "不明"

    def test_requires_login(self, client):
        res = client.get("/api/department/by-login-id?login_id=U001")
        assert res.status_code == 401

"""
EquipmentService 単体テスト（貸出・返却の3値ステータス対応）。

要件トレーサビリティ:
  要件ID: RQ-FT-LOAN-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT, RQ-DT-EQUIPMENT-RESERVED-STATUS
  設計ID: DS-FN-TEST-LOAN-RESERVED-FT-LOAN-EQUIPMENT, DS-FN-TEST-RETURN-UPDATE-STATUS-FT-RETURN-EQUIPMENT
  要件概要: status='reserved' でも貸出可能なこと、返却時に end_date < 返却日の予約が削除されステータスが更新されることを検証する。
  設計概要: SQLite インメモリDB で equipment・loan_state・reservation テーブルを再現して検証する。
  呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
  呼び出し元: pytest
"""
import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.equipment import Equipment
from app.models.user import User
from app.models.reservation import Reservation
from app.services.equipment_service import EquipmentService
from app.schemas.loan import LoanCreate


def _make_equipment(db: Session, equipment_id: str, status: str = "available"):
    eq = Equipment(equipment_id=equipment_id, name="テスト備品", status=status)
    db.add(eq)
    db.commit()
    return eq


def _make_user(db: Session, login_id: str = "user01"):
    import bcrypt
    pw_hash = bcrypt.hashpw("pass".encode(), bcrypt.gensalt()).decode()
    u = User(login_id=login_id, display_name="テスト利用者", password_hash=pw_hash, role="general")
    db.add(u)
    db.commit()
    return u


def _make_reservation(db: Session, equipment_id: str, user_login_id: str, start_date: str, end_date: str):
    r = Reservation(
        reservation_id=str(uuid.uuid4()),
        equipment_id=equipment_id,
        user_login_id=user_login_id,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(r)
    db.commit()
    return r


class TestLoanEquipmentReservedStatus:
    """DS-FN-TEST-LOAN-RESERVED-FT-LOAN-EQUIPMENT: status='reserved' でも貸出可能なこと。"""

    def test_loan_reserved_equipment_succeeds(self, db):
        _make_equipment(db, "EQ-LR-001", status="reserved")
        _make_user(db)
        service = EquipmentService(db)
        result = service.loan_equipment(
            "EQ-LR-001",
            LoanCreate(user_login_id="user01", loan_date="2026-07-01"),
        )
        assert result.status == "loaned"

    def test_loan_available_equipment_succeeds(self, db):
        _make_equipment(db, "EQ-LR-002", status="available")
        _make_user(db)
        service = EquipmentService(db)
        result = service.loan_equipment(
            "EQ-LR-002",
            LoanCreate(user_login_id="user01", loan_date="2026-07-01"),
        )
        assert result.status == "loaned"

    def test_loan_loaned_equipment_fails(self, db):
        from fastapi import HTTPException
        _make_equipment(db, "EQ-LR-003", status="loaned")
        _make_user(db)
        service = EquipmentService(db)
        with pytest.raises(HTTPException) as exc:
            service.loan_equipment(
                "EQ-LR-003",
                LoanCreate(user_login_id="user01", loan_date="2026-07-01"),
            )
        assert exc.value.status_code == 409


class TestReturnEquipmentStatusUpdate:
    """DS-FN-TEST-RETURN-UPDATE-STATUS-FT-RETURN-EQUIPMENT: 返却後のステータス更新。"""

    def test_return_with_no_reservations_sets_available(self, db):
        from app.models.loan_state import LoanState
        _make_equipment(db, "EQ-RT-001", status="loaned")
        _make_user(db)
        loan = LoanState(equipment_id="EQ-RT-001", user_login_id="user01", loan_date="2026-06-01")
        db.add(loan)
        db.commit()
        service = EquipmentService(db)
        result = service.return_equipment("EQ-RT-001")
        assert result.status == "available"

    def test_return_with_future_reservations_sets_reserved(self, db):
        import datetime
        from app.models.loan_state import LoanState
        _make_equipment(db, "EQ-RT-002", status="loaned")
        _make_user(db)
        loan = LoanState(equipment_id="EQ-RT-002", user_login_id="user01", loan_date="2026-06-01")
        db.add(loan)
        db.commit()
        future_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        future_end = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()
        _make_reservation(db, "EQ-RT-002", "user01", future_date, future_end)
        service = EquipmentService(db)
        result = service.return_equipment("EQ-RT-002")
        assert result.status == "reserved"

    def test_return_deletes_expired_reservations(self, db):
        import datetime
        from app.models.loan_state import LoanState
        from app.repositories.reservation import ReservationRepository
        _make_equipment(db, "EQ-RT-003", status="loaned")
        _make_user(db)
        loan = LoanState(equipment_id="EQ-RT-003", user_login_id="user01", loan_date="2026-06-01")
        db.add(loan)
        db.commit()
        past_start = (datetime.date.today() - datetime.timedelta(days=60)).isoformat()
        past_end = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        _make_reservation(db, "EQ-RT-003", "user01", past_start, past_end)
        service = EquipmentService(db)
        service.return_equipment("EQ-RT-003")
        repo = ReservationRepository(db)
        assert repo.count_by_equipment_id("EQ-RT-003") == 0

"""
ReservationRepository 単体テスト（count_overlapping 境界値含む）。

要件トレーサビリティ:
  要件ID: RQ-NF-RESERVATION-CONFLICT-PREVENTION, RQ-FT-MAKE-RESERVATION
  設計ID: DS-FN-TEST-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION
  要件概要: count_overlapping が重複あり/なし・境界値を正しく判定することを検証する。
  設計概要: SQLite インメモリDB で reservation テーブルを再現し、境界値テストを実施する。
  呼び出し先: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
  呼び出し元: pytest
"""
import uuid
import pytest
from app.models.equipment import Equipment
from app.models.user import User
from app.models.reservation import Reservation
from app.repositories.reservation import ReservationRepository


def _make_equipment(db, equipment_id="EQ-001", name="テスト備品"):
    eq = Equipment(equipment_id=equipment_id, name=name, status="available")
    db.add(eq)
    db.commit()
    return eq


def _make_user(db, login_id="user01", display_name="テスト利用者"):
    from app.core.config import settings
    import bcrypt
    pw_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()
    u = User(login_id=login_id, display_name=display_name, password_hash=pw_hash, role="general")
    db.add(u)
    db.commit()
    return u


def _make_reservation(db, equipment_id, user_login_id, start_date, end_date):
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


class TestCountOverlapping:
    """
    DS-FN-TEST-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION のテストクラス。
    """

    def test_no_overlap_returns_zero(self, db):
        _make_equipment(db)
        _make_user(db)
        _make_reservation(db, "EQ-001", "user01", "2026-06-01", "2026-06-05")
        repo = ReservationRepository(db)
        assert repo.count_overlapping("EQ-001", "2026-06-10", "2026-06-15") == 0

    def test_adjacent_before_returns_zero(self, db):
        """前接触（境界値）: 既存 end_date == 新規 start_date は重複なし"""
        _make_equipment(db)
        _make_user(db)
        _make_reservation(db, "EQ-001", "user01", "2026-06-01", "2026-06-05")
        repo = ReservationRepository(db)
        assert repo.count_overlapping("EQ-001", "2026-06-05", "2026-06-10") == 0

    def test_adjacent_after_returns_zero(self, db):
        """後接触（境界値）: 既存 start_date == 新規 end_date は重複なし"""
        _make_equipment(db)
        _make_user(db)
        _make_reservation(db, "EQ-001", "user01", "2026-06-10", "2026-06-15")
        repo = ReservationRepository(db)
        assert repo.count_overlapping("EQ-001", "2026-06-05", "2026-06-10") == 0

    def test_one_day_overlap_returns_one(self, db):
        """1日重複"""
        _make_equipment(db)
        _make_user(db)
        _make_reservation(db, "EQ-001", "user01", "2026-06-01", "2026-06-05")
        repo = ReservationRepository(db)
        assert repo.count_overlapping("EQ-001", "2026-06-04", "2026-06-08") == 1

    def test_full_containment_returns_one(self, db):
        """完全包含: 新規が既存を含む"""
        _make_equipment(db)
        _make_user(db)
        _make_reservation(db, "EQ-001", "user01", "2026-06-03", "2026-06-07")
        repo = ReservationRepository(db)
        assert repo.count_overlapping("EQ-001", "2026-06-01", "2026-06-10") == 1

    def test_different_equipment_no_overlap(self, db):
        """別の備品の予約は影響しない"""
        _make_equipment(db, "EQ-001")
        _make_equipment(db, "EQ-002", "別備品")
        _make_user(db)
        _make_reservation(db, "EQ-002", "user01", "2026-06-01", "2026-06-10")
        repo = ReservationRepository(db)
        assert repo.count_overlapping("EQ-001", "2026-06-01", "2026-06-10") == 0


class TestDeleteExpiredByEquipment:
    """
    delete_expired_by_equipment のテストクラス。
    """

    def test_deletes_expired_reservations(self, db):
        _make_equipment(db)
        _make_user(db)
        _make_reservation(db, "EQ-001", "user01", "2026-05-01", "2026-05-10")
        _make_reservation(db, "EQ-001", "user01", "2026-06-01", "2026-06-10")
        repo = ReservationRepository(db)
        repo.delete_expired_by_equipment("EQ-001", "2026-05-15")
        assert repo.count_by_equipment_id("EQ-001") == 1

    def test_keeps_future_reservations(self, db):
        _make_equipment(db)
        _make_user(db)
        _make_reservation(db, "EQ-001", "user01", "2026-06-01", "2026-06-10")
        repo = ReservationRepository(db)
        repo.delete_expired_by_equipment("EQ-001", "2026-05-15")
        assert repo.count_by_equipment_id("EQ-001") == 1

"""
予約サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-FT-VIEW-RESERVATION-CALENDAR,
          RQ-NF-RESERVATION-CONFLICT-PREVENTION
  設計ID: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
  要件概要: 予約CRUD・重複チェック・ステータス更新のビジネスロジックを提供する。
  設計概要: ReservationRepository と EquipmentRepository を組み合わせて予約管理ルールを適用する。
  呼び出し先: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY, DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
  呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
"""
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.reservation import ReservationRepository
from app.repositories.equipment import EquipmentRepository
from app.repositories.user import UserRepository
from app.schemas.reservation import ReservationCreate, ReservationResponse


class ReservationService:
    """
    予約管理のビジネスロジックを担うサービスクラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-NF-RESERVATION-CONFLICT-PREVENTION
      設計ID: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
      要件概要: 予約登録・キャンセル・一覧取得と各種制約チェックを提供する。
      設計概要: ReservationRepository・EquipmentRepository をコンポーズして予約管理ルールを適用する。
      呼び出し先: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY, DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
      呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
    """

    def __init__(self, db: Session):
        self.db = db
        self.reservation_repo = ReservationRepository(db)
        self.equipment_repo = EquipmentRepository(db)
        self.user_repo = UserRepository(db)

    def _to_response(self, reservation) -> ReservationResponse:
        """
        予約モデルをレスポンスに変換する。利用者表示名を付加する。

        要件トレーサビリティ:
          要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR
          設計ID: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
          要件概要: 予約一覧に予約者名を表示する。
          設計概要: user_login_id で UserRepository から display_name を取得して付与する。
          呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
        """
        user = self.user_repo.find_by_login_id(reservation.user_login_id)
        display_name = user.display_name if user else reservation.user_login_id
        return ReservationResponse(
            reservation_id=reservation.reservation_id,
            equipment_id=reservation.equipment_id,
            user_login_id=reservation.user_login_id,
            user_display_name=display_name,
            start_date=reservation.start_date,
            end_date=reservation.end_date,
        )

    def list_by_equipment(self, equipment_id: str) -> List[ReservationResponse]:
        """
        備品IDに紐づく全予約を開始日昇順で返す。

        Args:
            equipment_id (str): 対象備品ID。

        Returns:
            List[ReservationResponse]: 予約レスポンスのリスト。

        要件トレーサビリティ:
          要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR
          設計ID: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
          要件概要: カレンダー画面で備品の全予約一覧を表示する。
          設計概要: ReservationRepository.find_by_equipment_id を呼び出し _to_response で変換する。
          呼び出し先: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
        """
        reservations = self.reservation_repo.find_by_equipment_id(equipment_id)
        return [self._to_response(r) for r in reservations]

    def create(
        self,
        equipment_id: str,
        user_login_id: str,
        start_date: str,
        end_date: str,
    ) -> ReservationResponse:
        """
        予約を登録する。重複チェック後に予約レコードを作成し、備品ステータスを更新する。

        Args:
            equipment_id (str): 予約対象備品ID。
            user_login_id (str): 予約者ログインID。
            start_date (str): 予約開始日（YYYY-MM-DD）。
            end_date (str): 予約終了日（YYYY-MM-DD）。

        Returns:
            ReservationResponse: 作成された予約のレスポンス。

        Raises:
            HTTPException: 404 - 備品が存在しない場合。
            HTTPException: 409 - 重複する予約期間がある場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MAKE-RESERVATION, RQ-NF-RESERVATION-CONFLICT-PREVENTION, RQ-DT-EQUIPMENT-RESERVED-STATUS
          設計ID: DS-FN-PROCESS-CREATE-RESERVATION-FT-MAKE-RESERVATION, DS-FN-TRANSACTION-RESERVATION-DT-RESERVATION-ENTITY
          要件概要: 利用者が備品を期間指定で予約できる。重複期間は拒否する。
          設計概要: 重複チェック SELECT + reservation INSERT + equipment.status 更新を1トランザクションで実行する。
          呼び出し先: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY, DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
        """
        equipment = self.equipment_repo.find_by_id(equipment_id)
        if equipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="備品が見つかりません")

        overlap_count = self.reservation_repo.count_overlapping(equipment_id, start_date, end_date)
        if overlap_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="指定期間は既に予約されています",
            )

        data = ReservationCreate(
            start_date=start_date,
            end_date=end_date,
            user_login_id=user_login_id,
        )
        reservation = self.reservation_repo.create(data, user_login_id, equipment_id)

        if equipment.status == "available":
            equipment.status = "reserved"
            self.equipment_repo.update(equipment)

        self.db.commit()
        self.db.refresh(reservation)
        return self._to_response(reservation)

    def cancel(
        self,
        reservation_id: str,
        requesting_login_id: str,
        requesting_role: str,
    ) -> None:
        """
        予約をキャンセルする。予約者本人または管理者のみ実行可能。

        Args:
            reservation_id (str): キャンセルする予約ID。
            requesting_login_id (str): 操作者のログインID。
            requesting_role (str): 操作者のロール（"admin" または "general"）。

        Raises:
            HTTPException: 404 - 予約が存在しない場合。
            HTTPException: 403 - 本人でも管理者でもない場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-CANCEL-RESERVATION, RQ-DT-EQUIPMENT-RESERVED-STATUS
          設計ID: DS-FN-PROCESS-CANCEL-RESERVATION-FT-CANCEL-RESERVATION, DS-FN-TRANSACTION-CANCEL-RESERVATION-DT-RESERVATION-ENTITY
          要件概要: 予約者本人または管理者が予約をキャンセルできる。残予約0件で備品ステータスを available に戻す。
          設計概要: reservation DELETE + equipment.status 更新（残予約確認）を1トランザクションで実行する。
          呼び出し先: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY, DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
        """
        reservation = self.reservation_repo.find_by_id(reservation_id)
        if reservation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="予約が見つかりません")

        if requesting_role != "admin" and reservation.user_login_id != requesting_login_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="権限がありません",
            )

        equipment_id = reservation.equipment_id
        self.reservation_repo.delete(reservation_id)

        remaining = self.reservation_repo.count_by_equipment_id(equipment_id)
        equipment = self.equipment_repo.find_by_id(equipment_id)
        if equipment and remaining == 0 and equipment.status != "loaned":
            equipment.status = "available"
            self.equipment_repo.update(equipment)

        self.db.commit()

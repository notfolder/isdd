"""
予約リポジトリモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-RESERVATION-ENTITY, RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION
  設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
  要件概要: 予約エンティティの永続化操作（検索・作成・削除・カウント）を提供する。
  設計概要: SQLAlchemy Session を受け取り、Reservation モデルに対するCRUD操作をカプセル化する。
  呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
  呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate


class ReservationRepository:
    """
    予約エンティティのDB操作クラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-DT-RESERVATION-ENTITY
      設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
      要件概要: 予約エンティティのCRUD操作をDBレイヤーとして提供する。
      設計概要: Service 層から受け取った db セッションで Reservation テーブルを操作する。
      呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
      呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
    """

    def __init__(self, db: Session):
        self.db = db

    def find_by_equipment_id(self, equipment_id: str) -> List[Reservation]:
        """
        備品IDに紐づく全予約を開始日昇順で取得する。

        Args:
            equipment_id (str): 検索する備品ID。

        Returns:
            List[Reservation]: 予約レコードのリスト（開始日昇順）。

        要件トレーサビリティ:
          要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR
          設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
          要件概要: カレンダー画面で備品の全予約一覧を表示する。
          設計概要: equipment_id でフィルタし、start_date 昇順で返す。
          呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
        """
        return (
            self.db.query(Reservation)
            .filter(Reservation.equipment_id == equipment_id)
            .order_by(Reservation.start_date)
            .all()
        )

    def count_overlapping(self, equipment_id: str, start_date: str, end_date: str) -> int:
        """
        指定備品・指定期間と重複する予約件数をカウントする。

        重複条件: 既存予約の start_date < 新規 end_date AND 既存予約の end_date > 新規 start_date

        Args:
            equipment_id (str): 対象備品ID。
            start_date (str): 新規予約の開始日（YYYY-MM-DD）。
            end_date (str): 新規予約の終了日（YYYY-MM-DD）。

        Returns:
            int: 重複する予約件数。0 なら重複なし。

        要件トレーサビリティ:
          要件ID: RQ-NF-RESERVATION-CONFLICT-PREVENTION, RQ-FT-MAKE-RESERVATION
          設計ID: DS-FN-VALIDATE-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION
          要件概要: 同一備品への重複予約（1日以上重なる）を防ぐ。境界値（前後接触）は重複としない。
          設計概要: start_date < req_end AND end_date > req_start の条件でカウントする。
          呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
        """
        return (
            self.db.query(Reservation)
            .filter(
                and_(
                    Reservation.equipment_id == equipment_id,
                    Reservation.start_date < end_date,
                    Reservation.end_date > start_date,
                )
            )
            .count()
        )

    def create(self, data: ReservationCreate, user_login_id: str, equipment_id: str) -> Reservation:
        """
        予約レコードを新規作成する。reservation_id は UUID 自動生成。

        Args:
            data (ReservationCreate): 予約登録データ（start_date・end_date）。
            user_login_id (str): 予約者のログインID。
            equipment_id (str): 予約対象備品ID（パスパラメータから渡す）。

        Returns:
            Reservation: 作成された予約レコード。

        要件トレーサビリティ:
          要件ID: RQ-FT-MAKE-RESERVATION, RQ-DT-RESERVATION-ENTITY
          設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
          要件概要: 利用者が備品を期間指定で予約する。予約IDは自動生成する。
          設計概要: uuid4() で reservation_id を生成し、db.add + flush でセッションに追加する。
          呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
        """
        reservation = Reservation(
            reservation_id=str(uuid.uuid4()),
            equipment_id=equipment_id,
            user_login_id=user_login_id,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        self.db.add(reservation)
        self.db.flush()
        return reservation

    def find_by_id(self, reservation_id: str) -> Optional[Reservation]:
        """
        予約IDで1件取得する。

        Args:
            reservation_id (str): 検索する予約ID。

        Returns:
            Optional[Reservation]: 見つかった予約、または None。

        要件トレーサビリティ:
          要件ID: RQ-FT-CANCEL-RESERVATION
          設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
          要件概要: キャンセル対象の予約を取得する。
          設計概要: reservation_id を主キーとして1件検索する。
          呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
        """
        return (
            self.db.query(Reservation)
            .filter(Reservation.reservation_id == reservation_id)
            .first()
        )

    def delete(self, reservation_id: str) -> None:
        """
        予約IDで予約レコードを削除する。

        Args:
            reservation_id (str): 削除する予約ID。

        要件トレーサビリティ:
          要件ID: RQ-FT-CANCEL-RESERVATION
          設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
          要件概要: 利用者本人または管理者が予約をキャンセルする。
          設計概要: reservation_id でフィルタして delete クエリを実行し、flush する。
          呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
        """
        self.db.query(Reservation).filter(
            Reservation.reservation_id == reservation_id
        ).delete()
        self.db.flush()

    def count_by_equipment_id(self, equipment_id: str) -> int:
        """
        備品IDに紐づく有効予約件数をカウントする。

        Args:
            equipment_id (str): 対象備品ID。

        Returns:
            int: 有効予約件数。

        要件トレーサビリティ:
          要件ID: RQ-FT-CANCEL-RESERVATION, RQ-FT-RETURN-EQUIPMENT
          設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
          要件概要: キャンセル後・返却後の残予約数を確認して備品ステータスを決定する。
          設計概要: equipment_id でフィルタしてカウントする。
          呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION, DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        return (
            self.db.query(Reservation)
            .filter(Reservation.equipment_id == equipment_id)
            .count()
        )

    def delete_expired_by_equipment(self, equipment_id: str, before_date: str) -> None:
        """
        end_date が before_date より前の予約レコードを全て削除する。返却処理時に呼び出す。

        Args:
            equipment_id (str): 対象備品ID。
            before_date (str): この日付より前に終了する予約を削除する（YYYY-MM-DD形式）。

        要件トレーサビリティ:
          要件ID: RQ-DT-RESERVATION-RETENTION, RQ-FT-RETURN-EQUIPMENT
          設計ID: DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY
          要件概要: 返却操作時に end_date が返却日より前の予約を自動削除する。
          設計概要: equipment_id と end_date < before_date でフィルタして一括削除する。
          呼び出し先: DS-SC-RESERVATION-DT-RESERVATION-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        self.db.query(Reservation).filter(
            and_(
                Reservation.equipment_id == equipment_id,
                Reservation.end_date < before_date,
            )
        ).delete()
        self.db.flush()

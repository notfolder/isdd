"""
備品サービスモジュール（CRUD・貸出・返却ビジネスロジック）。

要件トレーサビリティ:
  要件ID: RQ-FT-LIST-EQUIPMENT
  設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
  要件概要: 全備品の状態確認・登録・編集・削除・貸出・返却を行う。
  設計概要: EquipmentServiceクラスが備品CRUD・貸出・返却・業務制約チェックを担う。
  呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-LENDING-DT-ENTITY-LENDING
  呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-RECORD-LENDING-FT-RECORD-LENDING
"""

import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.equipment import Equipment
from app.models.lending import LendingRecord
from app.models.user import User
from app.schemas.equipment import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse,
    LendingCreate, LendingInfo,
)


class EquipmentService:
    """
    備品ビジネスロジックサービスクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      要件概要: 全備品CRUD・貸出・返却・業務制約（貸出中削除不可）を担う。
      設計概要: 各操作を個別メソッドで実装。削除時・貸出時は貸出記録存在チェックを実施する。
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-LENDING-DT-ENTITY-LENDING
      呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
    """

    def list_all(self, db: Session) -> List[EquipmentResponse]:
        """
        全備品を一覧取得する（貸出情報含む）。

        Args:
            db (Session): DBセッション。

        Returns:
            List[EquipmentResponse]: 全備品のレスポンスリスト。

        要件トレーサビリティ:
          要件ID: RQ-FT-LIST-EQUIPMENT
          設計ID: DS-FN-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
          要件概要: 全備品の管理番号・備品名・状態・貸出情報を一覧で取得する。
          設計概要: equipmentテーブルを全件取得し、lending_recordsをJOINして状態を判定する。
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-LENDING-DT-ENTITY-LENDING
          呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
        """
        items = db.query(Equipment).all()
        result = []
        for item in items:
            lending_info = None
            if item.lending_record:
                lr = item.lending_record
                user = db.query(User).filter(User.id == lr.user_id).first()
                lending_info = LendingInfo(
                    user_id=lr.user_id,
                    user_name=user.name if user else "",
                    lend_date=lr.lend_date,
                    expected_return_date=lr.expected_return_date,
                )
            result.append(EquipmentResponse(
                management_number=item.management_number,
                name=item.name,
                status="貸出中" if item.lending_record else "在庫中",
                lending_info=lending_info,
            ))
        return result

    def create(self, db: Session, data: EquipmentCreate) -> EquipmentResponse:
        """
        備品を新規登録する。

        Args:
            db (Session): DBセッション。
            data (EquipmentCreate): 登録データ。

        Returns:
            EquipmentResponse: 登録された備品レスポンス。

        Raises:
            HTTPException: 409 管理番号重複の場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-CREATE-EQUIPMENT
          設計ID: DS-FN-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
          要件概要: 管理番号と備品名を受け取り備品を登録する。管理番号はシステム内で一意。
          設計概要: 管理番号の重複チェック後にINSERT。重複時は409 Conflictを返す。
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT
          呼び出し元設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
        """
        existing = db.query(Equipment).filter(
            Equipment.management_number == data.management_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="この管理番号は既に使用されています",
            )
        item = Equipment(management_number=data.management_number, name=data.name)
        db.add(item)
        db.commit()
        db.refresh(item)
        return EquipmentResponse(
            management_number=item.management_number,
            name=item.name,
            status="在庫中",
        )

    def update(self, db: Session, management_number: str, data: EquipmentUpdate) -> EquipmentResponse:
        """
        備品情報を更新する。

        Args:
            db (Session): DBセッション。
            management_number (str): 更新対象の管理番号。
            data (EquipmentUpdate): 更新データ。

        Returns:
            EquipmentResponse: 更新後の備品レスポンス。

        Raises:
            HTTPException: 404 備品不在の場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-UPDATE-EQUIPMENT
          設計ID: DS-FN-UPDATE-EQUIPMENT-FT-UPDATE-EQUIPMENT
          要件概要: 備品名を更新する。存在しない管理番号の場合は404を返す。
          設計概要: 管理番号でEquipmentを検索し、nameを更新してcommitする。
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT
          呼び出し元設計ID: DS-IF-UPDATE-EQUIPMENT-FT-UPDATE-EQUIPMENT
        """
        item = db.query(Equipment).filter(
            Equipment.management_number == management_number
        ).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="該当する備品が見つかりません")
        item.name = data.name
        db.commit()
        db.refresh(item)
        return EquipmentResponse(
            management_number=item.management_number,
            name=item.name,
            status="貸出中" if item.lending_record else "在庫中",
        )

    def delete(self, db: Session, management_number: str) -> None:
        """
        備品を削除する（貸出中は削除不可）。

        Args:
            db (Session): DBセッション。
            management_number (str): 削除対象の管理番号。

        Raises:
            HTTPException: 404 備品不在、409 貸出中の場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-DELETE-EQUIPMENT
          設計ID: DS-FN-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT
          要件概要: 備品を削除する。貸出中の備品は削除できない（先に返却処理が必要）。
          設計概要: lending_record存在チェック後にDELETE。貸出中は409 Conflictを返す。
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT, DS-SC-LENDING-DT-ENTITY-LENDING
          呼び出し元設計ID: DS-IF-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT
        """
        item = db.query(Equipment).filter(
            Equipment.management_number == management_number
        ).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="該当する備品が見つかりません")
        if item.lending_record:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="貸出中の備品は削除できません。先に返却処理をしてください",
            )
        db.delete(item)
        db.commit()

    def record_lend(self, db: Session, management_number: str, data: LendingCreate) -> EquipmentResponse:
        """
        貸出処理を記録する。

        Args:
            db (Session): DBセッション。
            management_number (str): 貸出対象の管理番号。
            data (LendingCreate): 貸出データ（ユーザーID・貸出日・返却予定日）。

        Returns:
            EquipmentResponse: 貸出後の備品レスポンス。

        Raises:
            HTTPException: 404 備品不在、409 既に貸出中、422 日付不正。

        要件トレーサビリティ:
          要件ID: RQ-FT-RECORD-LENDING
          設計ID: DS-FN-RECORD-LENDING-FT-RECORD-LENDING
          要件概要: 在庫中の備品に貸出先・貸出日・返却予定日を登録して「貸出中」に変更する。
          設計概要: 備品の存在・在庫状態確認後にlending_recordsにINSERT。返却予定日>=貸出日のバリデーションを行う。
          呼び出し先設計ID: DS-SC-LENDING-DT-ENTITY-LENDING, DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT
          呼び出し元設計ID: DS-IF-RECORD-LENDING-FT-RECORD-LENDING
        """
        item = db.query(Equipment).filter(
            Equipment.management_number == management_number
        ).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="該当する備品が見つかりません")
        if item.lending_record:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="この備品は既に貸出中です",
            )
        if data.expected_return_date < data.lend_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="返却予定日は貸出日以降に設定してください",
            )
        user = db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="該当するユーザーが見つかりません")
        lr = LendingRecord(
            equipment_number=management_number,
            user_id=data.user_id,
            lend_date=data.lend_date,
            expected_return_date=data.expected_return_date,
        )
        db.add(lr)
        db.commit()
        db.refresh(lr)
        return EquipmentResponse(
            management_number=item.management_number,
            name=item.name,
            status="貸出中",
            lending_info=LendingInfo(
                user_id=lr.user_id,
                user_name=user.name,
                lend_date=lr.lend_date,
                expected_return_date=lr.expected_return_date,
            ),
        )

    def record_return(self, db: Session, management_number: str) -> None:
        """
        返却処理を記録する（貸出記録を物理削除）。

        Args:
            db (Session): DBセッション。
            management_number (str): 返却対象の管理番号。

        Raises:
            HTTPException: 404 備品不在または貸出中でない場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-RECORD-RETURN
          設計ID: DS-FN-RECORD-RETURN-FT-RECORD-RETURN
          要件概要: 貸出中の備品の返却を処理し「在庫中」に変更する。貸出記録は物理削除（履歴なし）。
          設計概要: lending_recordsの対象レコードをDELETEする。備品や貸出記録が不在の場合は404を返す。
          呼び出し先設計ID: DS-SC-LENDING-DT-ENTITY-LENDING
          呼び出し元設計ID: DS-IF-RECORD-RETURN-FT-RECORD-RETURN
        """
        item = db.query(Equipment).filter(
            Equipment.management_number == management_number
        ).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="該当する備品が見つかりません")
        if not item.lending_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="この備品は貸出中ではありません",
            )
        db.delete(item.lending_record)
        db.commit()


equipment_service = EquipmentService()

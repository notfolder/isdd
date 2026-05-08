"""
備品サービス：備品のCRUD操作と業務制約チェック。

要件トレーサビリティ:
  要件ID: RQ-FT-LIST-EQUIPMENT, RQ-FT-CREATE-EQUIPMENT, RQ-FT-EDIT-EQUIPMENT, RQ-FT-DELETE-EQUIPMENT
  設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
  要件概要: 備品の登録・参照・更新・削除を行う。貸出中の備品は削除不可
  設計概要: list_all, create(重複asset_numberは409), update(未存在は404), delete(貸出中は409)を実装する
  呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY, DS-FN-CHECK-EQUIPMENT-DELETABLE-FT-DELETE-EQUIPMENT
  呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.equipment import Equipment
from app.models.loan import Loan
from app.models.user import User
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse


class EquipmentService:
    """
    備品サービスクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      要件概要: 備品のCRUD操作を提供する
      設計概要: list_all, create, update, deleteメソッドを実装する
      呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
      呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
    """

    def list_all(self, db: Session) -> List[EquipmentResponse]:
        """
        全備品一覧を取得する（貸出中の場合は貸出先ユーザー名・貸出日・貸出IDを含む）。

        Args:
            db (Session): DBセッション

        Returns:
            List[EquipmentResponse]: 備品一覧

        要件トレーサビリティ:
          要件ID: RQ-FT-LIST-EQUIPMENT
          設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
          要件概要: 備品の状態一覧を表示する。貸出中の備品には貸出先ユーザー名を表示
          設計概要: 全備品をSELECTし、貸出中の場合はloansとusersをJOINして貸出情報を付与する
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
        """
        equipments = db.query(Equipment).all()
        result = []
        for eq in equipments:
            # 未返却の貸出記録を検索
            active_loan = (
                db.query(Loan)
                .filter(Loan.equipment_id == eq.id, Loan.returned_at == None)
                .first()
            )
            borrower_name = None
            lent_at = None
            loan_id = None
            if active_loan:
                borrower = db.query(User).filter(User.id == active_loan.user_id).first()
                borrower_name = borrower.username if borrower else None
                lent_at = active_loan.lent_at
                loan_id = active_loan.id
            result.append(
                EquipmentResponse(
                    id=eq.id,
                    asset_number=eq.asset_number,
                    name=eq.name,
                    status=eq.status,
                    borrower_name=borrower_name,
                    lent_at=lent_at,
                    loan_id=loan_id,
                )
            )
        return result

    def create(self, db: Session, data: EquipmentCreate) -> Equipment:
        """
        備品を新規登録する。

        Args:
            db (Session): DBセッション
            data (EquipmentCreate): 登録データ

        Returns:
            Equipment: 登録された備品

        Raises:
            HTTPException: 重複資産管理番号の場合409

        要件トレーサビリティ:
          要件ID: RQ-FT-CREATE-EQUIPMENT
          設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
          要件概要: 備品を登録し、台帳に新しい備品を追加する
          設計概要: 重複asset_numberは409 Conflictを返す。登録後はstatus='available'
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
        """
        existing = db.query(Equipment).filter(Equipment.asset_number == data.asset_number).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="この資産管理番号は既に使用されています",
            )
        equipment = Equipment(
            asset_number=data.asset_number,
            name=data.name,
            status="available",
        )
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        return equipment

    def update(self, db: Session, equipment_id: int, data: EquipmentUpdate) -> Equipment:
        """
        備品情報を更新する。

        Args:
            db (Session): DBセッション
            equipment_id (int): 備品ID
            data (EquipmentUpdate): 更新データ

        Returns:
            Equipment: 更新された備品

        Raises:
            HTTPException: 備品未存在は404、重複asset_numberは409

        要件トレーサビリティ:
          要件ID: RQ-FT-EDIT-EQUIPMENT
          設計ID: DS-IF-UPDATE-EQUIPMENT-FT-EDIT-EQUIPMENT
          要件概要: 備品名・資産管理番号の誤りを修正できる
          設計概要: 指定IDの備品を更新する。未存在は404 Not Found
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元設計ID: DS-IF-UPDATE-EQUIPMENT-FT-EDIT-EQUIPMENT
        """
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if equipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="備品が見つかりません",
            )
        if data.asset_number is not None:
            existing = db.query(Equipment).filter(
                Equipment.asset_number == data.asset_number,
                Equipment.id != equipment_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="この資産管理番号は既に使用されています",
                )
            equipment.asset_number = data.asset_number
        if data.name is not None:
            equipment.name = data.name
        db.commit()
        db.refresh(equipment)
        return equipment

    def delete(self, db: Session, equipment_id: int) -> None:
        """
        備品を削除する。

        Args:
            db (Session): DBセッション
            equipment_id (int): 備品ID

        Raises:
            HTTPException: 備品未存在は404、貸出中は409

        要件トレーサビリティ:
          要件ID: RQ-FT-DELETE-EQUIPMENT
          設計ID: DS-FN-CHECK-EQUIPMENT-DELETABLE-FT-DELETE-EQUIPMENT
          要件概要: 廃棄した備品をシステムから削除できる。貸出中の備品は削除不可
          設計概要: statusが'lent'の場合は409 Conflictを返す
          呼び出し先設計ID: DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元設計ID: DS-IF-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT
        """
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if equipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="備品が見つかりません",
            )
        if equipment.status == "lent":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="貸出中の備品は削除できません",
            )
        db.delete(equipment)
        db.commit()


equipment_service = EquipmentService()

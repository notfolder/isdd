"""
貸出サービス：貸出登録と返却登録のトランザクション管理。

要件トレーサビリティ:
  要件ID: RQ-FT-LEND-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT
  設計ID: DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
  要件概要: 貸出記録を登録し備品ステータスを更新する。返却時は返却日を記録し備品を貸出可能に戻す
  設計概要: lend(トランザクション: loans INSERT + equipment.status='lent')、return_equipment(トランザクション: loans.returned_at記録 + equipment.status='available')を実装する
  呼び出し先設計ID: DS-SC-LOAN-DT-LOAN-ENTITY, DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
  呼び出し元設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT, DS-IF-RETURN-EQUIPMENT-FT-RETURN-EQUIPMENT
"""

from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.equipment import Equipment
from app.models.loan import Loan
from app.schemas.loan import LoanCreate, LoanResponse


class LoanService:
    """
    貸出サービスクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-LEND-EQUIPMENT
      設計ID: DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
      要件概要: 貸出・返却業務ロジックを提供する
      設計概要: lend, return_equipmentメソッドをトランザクションで実装する
      呼び出し先設計ID: DS-SC-LOAN-DT-LOAN-ENTITY
      呼び出し元設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT
    """

    def lend(self, db: Session, data: LoanCreate) -> Loan:
        """
        備品を貸し出す（トランザクション：loans INSERT + equipment.status='lent'）。

        Args:
            db (Session): DBセッション
            data (LoanCreate): 貸出データ（equipment_id, user_id）

        Returns:
            Loan: 貸出記録

        Raises:
            HTTPException: 備品未存在は404、既に貸出中は409

        要件トレーサビリティ:
          要件ID: RQ-FT-LEND-EQUIPMENT
          設計ID: DS-FN-LEND-FT-LEND-EQUIPMENT
          要件概要: 管理者が備品を特定ユーザーに割り当て、状態を「貸出中」にする
          設計概要: loans INSERTとequipment.status更新をトランザクションで実行する
          呼び出し先設計ID: DS-SC-LOAN-DT-LOAN-ENTITY, DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT
        """
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if equipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="備品が見つかりません",
            )
        if equipment.status == "lent":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="この備品は既に貸出中です",
            )
        # トランザクション: loans INSERT + equipment.status = 'lent'
        loan = Loan(
            equipment_id=data.equipment_id,
            user_id=data.user_id,
            lent_at=date.today(),
        )
        db.add(loan)
        equipment.status = "lent"
        db.commit()
        db.refresh(loan)
        return loan

    def return_equipment(self, db: Session, loan_id: int) -> Loan:
        """
        備品を返却する（トランザクション：loans.returned_at記録 + equipment.status='available'）。

        Args:
            db (Session): DBセッション
            loan_id (int): 貸出記録ID

        Returns:
            Loan: 更新された貸出記録

        Raises:
            HTTPException: 貸出記録未存在は404

        要件トレーサビリティ:
          要件ID: RQ-FT-RETURN-EQUIPMENT
          設計ID: DS-IF-RETURN-EQUIPMENT-FT-RETURN-EQUIPMENT
          要件概要: 管理者が備品の状態を「貸出可能」に戻す
          設計概要: loans.returned_at記録とequipment.status='available'更新をトランザクションで実行する
          呼び出し先設計ID: DS-SC-LOAN-DT-LOAN-ENTITY, DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元設計ID: DS-IF-RETURN-EQUIPMENT-FT-RETURN-EQUIPMENT
        """
        loan = db.query(Loan).filter(Loan.id == loan_id, Loan.returned_at == None).first()
        if loan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="貸出記録が見つかりません",
            )
        equipment = db.query(Equipment).filter(Equipment.id == loan.equipment_id).first()
        # トランザクション: loans.returned_at記録 + equipment.status = 'available'
        loan.returned_at = date.today()
        equipment.status = "available"
        db.commit()
        db.refresh(loan)
        return loan


loan_service = LoanService()

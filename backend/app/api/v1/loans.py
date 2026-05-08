"""
貸出エンドポイント：貸出登録と返却登録。

要件トレーサビリティ:
  要件ID: RQ-FT-LEND-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT
  設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT, DS-IF-RETURN-EQUIPMENT-FT-RETURN-EQUIPMENT
  要件概要: 管理者が備品を特定ユーザーに貸し出し、返却操作で貸出可能に戻す
  設計概要: POST /api/loans(管理者)、PUT /api/loans/{id}/return(管理者)を実装する
  呼び出し先設計ID: DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanResponse
from app.services.loan_service import loan_service

router = APIRouter()


@router.post("/loans", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    data: LoanCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    備品貸出登録エンドポイント（管理者のみ）。

    Args:
        data (LoanCreate): 貸出データ（equipment_id, user_id）
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    Returns:
        LoanResponse: 貸出記録

    要件トレーサビリティ:
      要件ID: RQ-FT-LEND-EQUIPMENT
      設計ID: DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT
      要件概要: 管理者が備品を特定ユーザーに割り当て、状態を「貸出中」にする
      設計概要: POST /api/loansで201 Createdを返す。管理者専用。トランザクションで実行
      呼び出し先設計ID: DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return loan_service.lend(db, data)


@router.put("/loans/{loan_id}/return", response_model=LoanResponse)
def return_equipment(
    loan_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    備品返却登録エンドポイント（管理者のみ）。

    Args:
        loan_id (int): 貸出記録ID
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    Returns:
        LoanResponse: 更新された貸出記録

    要件トレーサビリティ:
      要件ID: RQ-FT-RETURN-EQUIPMENT
      設計ID: DS-IF-RETURN-EQUIPMENT-FT-RETURN-EQUIPMENT
      要件概要: 管理者が備品の状態を「貸出可能」に戻す
      設計概要: PUT /api/loans/{id}/returnで200 OKを返す。管理者専用。トランザクションで実行
      呼び出し先設計ID: DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return loan_service.return_equipment(db, loan_id)

"""
備品APIルーターモジュール（CRUD・貸出・返却）。

要件トレーサビリティ:
  要件ID: RQ-FT-LIST-EQUIPMENT
  設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
  要件概要: 全備品の取得・登録・更新・削除・貸出・返却のエンドポイントを提供する。
  設計概要: FastAPIルーターでGET/POST/PUT/DELETE /api/equipment エンドポイントを定義する。
  呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
  呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse, LendingCreate
from app.services.equipment_service import equipment_service

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


def list_equipment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EquipmentResponse]:
    """
    全備品一覧を取得する（全ユーザーアクセス可）。

    Args:
        db (Session): DBセッション。
        current_user (User): 認証済みユーザー。

    Returns:
        List[EquipmentResponse]: 全備品と貸出情報のリスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
      要件概要: 全備品の管理番号・備品名・状態・貸出情報を全ユーザーが閲覧できる。
      設計概要: GET /api/equipment で全件取得。認証必須。EquipmentService.list_allに委譲する。
      呼び出し先設計ID: DS-FN-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
      呼び出し元設計ID: DS-CL-EQUIPMENT-LIST-VIEW-UI-EQUIPMENT-LIST-SCREEN
    """
    return equipment_service.list_all(db)


def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> EquipmentResponse:
    """
    備品を新規登録する（管理者のみ）。

    Args:
        data (EquipmentCreate): 登録データ。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    Returns:
        EquipmentResponse: 登録された備品。

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-EQUIPMENT
      設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
      要件概要: 管理者が備品を登録する。管理番号と備品名が必須。管理番号は一意。
      設計概要: POST /api/equipment。管理者権限必須。EquipmentService.createに委譲する。
      呼び出し先設計ID: DS-FN-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN
    """
    return equipment_service.create(db, data)


def update_equipment(
    management_number: str,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> EquipmentResponse:
    """
    備品情報を更新する（管理者のみ）。

    Args:
        management_number (str): 更新対象管理番号（パスパラメータ）。
        data (EquipmentUpdate): 更新データ。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    Returns:
        EquipmentResponse: 更新後の備品。

    要件トレーサビリティ:
      要件ID: RQ-FT-UPDATE-EQUIPMENT
      設計ID: DS-IF-UPDATE-EQUIPMENT-FT-UPDATE-EQUIPMENT
      要件概要: 管理者が備品名を更新する。存在しない管理番号は404を返す。
      設計概要: PUT /api/equipment/{management_number}。管理者権限必須。EquipmentService.updateに委譲。
      呼び出し先設計ID: DS-FN-UPDATE-EQUIPMENT-FT-UPDATE-EQUIPMENT, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN
    """
    return equipment_service.update(db, management_number, data)


def delete_equipment(
    management_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """
    備品を削除する（管理者のみ・貸出中不可）。

    Args:
        management_number (str): 削除対象管理番号（パスパラメータ）。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    要件トレーサビリティ:
      要件ID: RQ-FT-DELETE-EQUIPMENT
      設計ID: DS-IF-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT
      要件概要: 管理者が備品を削除する。貸出中の備品は削除できない。
      設計概要: DELETE /api/equipment/{management_number}。管理者権限必須。EquipmentService.deleteに委譲。
      呼び出し先設計ID: DS-FN-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-EQUIPMENT-LIST-VIEW-UI-EQUIPMENT-LIST-SCREEN
    """
    equipment_service.delete(db, management_number)


def lend_equipment(
    management_number: str,
    data: LendingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> EquipmentResponse:
    """
    備品の貸出処理を記録する（管理者のみ）。

    Args:
        management_number (str): 貸出対象管理番号（パスパラメータ）。
        data (LendingCreate): 貸出データ。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    Returns:
        EquipmentResponse: 貸出後の備品情報。

    要件トレーサビリティ:
      要件ID: RQ-FT-RECORD-LENDING
      設計ID: DS-IF-RECORD-LENDING-FT-RECORD-LENDING
      要件概要: 管理者が在庫中の備品を貸出中に変更する。貸出先・貸出日・返却予定日を記録する。
      設計概要: POST /api/equipment/{id}/lend。管理者権限必須。EquipmentService.record_lendに委譲。
      呼び出し先設計ID: DS-FN-RECORD-LENDING-FT-RECORD-LENDING, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-LENDING-MODAL-UI-LENDING-MODAL
    """
    return equipment_service.record_lend(db, management_number, data)


def return_equipment(
    management_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """
    備品の返却処理を記録する（管理者のみ）。

    Args:
        management_number (str): 返却対象管理番号（パスパラメータ）。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    要件トレーサビリティ:
      要件ID: RQ-FT-RECORD-RETURN
      設計ID: DS-IF-RECORD-RETURN-FT-RECORD-RETURN
      要件概要: 管理者が貸出中の備品を在庫中に変更する。貸出記録を物理削除する（履歴なし）。
      設計概要: POST /api/equipment/{id}/return。管理者権限必須。EquipmentService.record_returnに委譲。
      呼び出し先設計ID: DS-FN-RECORD-RETURN-FT-RECORD-RETURN, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-RETURN-DIALOG-UI-RETURN-DIALOG
    """
    equipment_service.record_return(db, management_number)


router.get("/", response_model=List[EquipmentResponse])(list_equipment)
router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)(create_equipment)
router.put("/{management_number}", response_model=EquipmentResponse)(update_equipment)
router.delete("/{management_number}", status_code=status.HTTP_204_NO_CONTENT)(delete_equipment)
router.post("/{management_number}/lend", response_model=EquipmentResponse)(lend_equipment)
router.post("/{management_number}/return", status_code=status.HTTP_204_NO_CONTENT)(return_equipment)

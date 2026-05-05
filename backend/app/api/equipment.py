"""
備品APIルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT
  設計ID: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
  要件概要: 備品のCRUD操作・貸出・返却APIエンドポイントを提供する。
  設計概要: FastAPI Router で /api/equipment の各エンドポイントを定義する。GET は認証ユーザー、それ以外は管理者のみ。
  呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
  呼び出し元: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_admin, get_current_user
from app.models.user import User
from app.services.equipment_service import EquipmentService
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse
from app.schemas.loan import LoanCreate

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


@router.get("", response_model=List[EquipmentResponse])
def list_equipment(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    全備品一覧を取得する。

    Args:
        db (Session): DBセッション。
        _current_user (User): ログイン確認用（管理者・一般利用者ともにアクセス可）。

    Returns:
        List[EquipmentResponse]: 貸出情報付き全備品のリスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-NF-ROLE-ACCESS
      設計ID: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
      要件概要: ログイン済みユーザーが全備品と貸出状態を一覧で確認できる。一般利用者も閲覧可能。
      設計概要: GET /api/equipment。get_current_user（管理者・一般利用者共通）で認証を確認する。
      呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
      呼び出し元: フロントエンド DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
    """
    return EquipmentService(db).list_equipment()


@router.post("", response_model=EquipmentResponse)
def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    備品を新規作成する。

    Args:
        data (EquipmentCreate): 作成する備品データ（equipment_id・name）。
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用。

    Returns:
        EquipmentResponse: 作成された備品。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-NF-ROLE-ACCESS
      設計ID: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
      要件概要: 管理者が新しい備品を登録できる。一般利用者は実行不可。
      設計概要: POST /api/equipment。require_admin で管理者権限を確認してから作成する。
      呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
      呼び出し元: フロントエンド DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
    """
    return EquipmentService(db).create_equipment(data)


@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: str,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    備品情報を更新する。

    Args:
        equipment_id (str): 更新対象の備品ID。
        data (EquipmentUpdate): 更新データ（name のみ）。
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用。

    Returns:
        EquipmentResponse: 更新後の備品。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
      要件概要: 管理者が備品名称を更新できる。
      設計概要: PUT /api/equipment/{equipment_id}。EquipmentService.update_equipment() に委譲する。
      呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
      呼び出し元: フロントエンド DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
    """
    return EquipmentService(db).update_equipment(equipment_id, data)


@router.delete("/{equipment_id}")
def delete_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    備品を削除する。

    Args:
        equipment_id (str): 削除対象の備品ID。
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用。

    Returns:
        dict: 削除完了メッセージ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
      要件概要: 管理者が不要な備品を削除できる。貸出中は削除禁止。
      設計概要: DELETE /api/equipment/{equipment_id}。EquipmentService.delete_equipment() に委譲する。
      呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
      呼び出し元: フロントエンド DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
    """
    EquipmentService(db).delete_equipment(equipment_id)
    return {"message": "削除しました"}


@router.post("/{equipment_id}/loan", response_model=EquipmentResponse)
def loan_equipment(
    equipment_id: str,
    data: LoanCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    備品を貸出する。

    Args:
        equipment_id (str): 貸出対象の備品ID。
        data (LoanCreate): 貸出データ（user_login_id・loan_date）。
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用。

    Returns:
        EquipmentResponse: 貸出後の備品（status='loaned'）。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOAN-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
      要件概要: 管理者が指定の備品を指定の利用者に貸出できる。
      設計概要: POST /api/equipment/{equipment_id}/loan。EquipmentService.loan_equipment() に委譲する。
      呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
      呼び出し元: フロントエンド DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
    """
    return EquipmentService(db).loan_equipment(equipment_id, data)


@router.post("/{equipment_id}/return", response_model=EquipmentResponse)
def return_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    備品を返却する。

    Args:
        equipment_id (str): 返却対象の備品ID。
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用。

    Returns:
        EquipmentResponse: 返却後の備品（status='available'）。

    要件トレーサビリティ:
      要件ID: RQ-FT-RETURN-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
      要件概要: 管理者が貸出中の備品を返却処理できる。
      設計概要: POST /api/equipment/{equipment_id}/return。EquipmentService.return_equipment() に委譲する。
      呼び出し先: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
      呼び出し元: フロントエンド DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
    """
    return EquipmentService(db).return_equipment(equipment_id)

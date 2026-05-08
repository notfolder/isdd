"""
備品エンドポイント：備品の一覧・登録・更新・削除。

要件トレーサビリティ:
  要件ID: RQ-FT-LIST-EQUIPMENT, RQ-FT-CREATE-EQUIPMENT, RQ-FT-EDIT-EQUIPMENT, RQ-FT-DELETE-EQUIPMENT
  設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT, DS-IF-UPDATE-EQUIPMENT-FT-EDIT-EQUIPMENT, DS-IF-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT
  要件概要: 全ユーザーが備品一覧を参照可能。管理者のみ登録・更新・削除が可能
  設計概要: GET /api/equipment(全員)、POST /api/equipment(管理者)、PUT /api/equipment/{id}(管理者)、DELETE /api/equipment/{id}(管理者)を実装する
  呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse
from app.services.equipment_service import equipment_service

router = APIRouter()


@router.get("/equipment", response_model=List[EquipmentResponse])
def list_equipment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    備品一覧を取得する（全ユーザー共通）。

    Args:
        current_user (User): 現在のユーザー（認証必須）
        db (Session): DBセッション

    Returns:
        List[EquipmentResponse]: 備品一覧

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
      要件概要: 備品の状態一覧を表示する。貸出中の備品には貸出先ユーザー名を表示
      設計概要: GET /api/equipmentで全備品を返す。認証必須、役割制限なし
      呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return equipment_service.list_all(db)


@router.post("/equipment", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(
    data: EquipmentCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    備品を新規登録する（管理者のみ）。

    Args:
        data (EquipmentCreate): 登録データ
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    Returns:
        EquipmentResponse: 登録された備品

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-EQUIPMENT
      設計ID: DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT
      要件概要: 新規備品をシステムに登録できる（管理者のみ）
      設計概要: POST /api/equipmentで201 Createdを返す。管理者専用
      呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return equipment_service.create(db, data)


@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    備品情報を更新する（管理者のみ）。

    Args:
        equipment_id (int): 備品ID
        data (EquipmentUpdate): 更新データ
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    Returns:
        EquipmentResponse: 更新された備品

    要件トレーサビリティ:
      要件ID: RQ-FT-EDIT-EQUIPMENT
      設計ID: DS-IF-UPDATE-EQUIPMENT-FT-EDIT-EQUIPMENT
      要件概要: 備品名・資産管理番号の誤りを修正できる（管理者のみ）
      設計概要: PUT /api/equipment/{id}で更新する。管理者専用、未存在は404
      呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return equipment_service.update(db, equipment_id, data)


@router.delete("/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    備品を削除する（管理者のみ）。

    Args:
        equipment_id (int): 備品ID
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    要件トレーサビリティ:
      要件ID: RQ-FT-DELETE-EQUIPMENT
      設計ID: DS-IF-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT
      要件概要: 廃棄した備品をシステムから削除できる。貸出中の備品は削除不可
      設計概要: DELETE /api/equipment/{id}で204を返す。貸出中は409、未存在は404
      呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    equipment_service.delete(db, equipment_id)

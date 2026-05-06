"""
UserRouter - 利用者関連のAPIエンドポイント

要件トレーサビリティ:
  要件ID: RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST
  設計ID: DS-CL-USER-ROUTER-FT-REGISTER-USER
  要件概要: 利用者の登録、編集、削除、一覧表示を行うAPIを提供する
  設計概要: RESTful APIエンドポイントを提供し、JWT認証と権限チェックを行う
  呼び出し先: DS-CL-USER-SERVICE-FT-REGISTER-USER, DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
  呼び出し元: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN (ApiClient)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from src.schemas.schemas import UserResponse, UserCreate, UserUpdate
from src.services.user_service import user_service
from src.database.database_manager import db_manager
from src.routers.item_router import get_current_user, require_admin

router = APIRouter(prefix="/api/users", tags=["利用者"])


@router.get("", response_model=List[UserResponse])
def get_users(current_user: dict = Depends(require_admin)):
    """
    利用者一覧を取得する
    
    要件ID: RQ-FT-VIEW-USER-LIST
    設計ID: DS-IF-GET-USERS-API-FT-VIEW-USER-LIST
    要件概要: 利用者一覧を表示する（管理者のみ）
    設計概要: 全利用者を取得する
    
    Returns:
        List[UserResponse]: 利用者リスト
    """
    db_conn = db_manager.connect()
    try:
        users = user_service.get_all_users(db_conn)
        return users
    finally:
        db_conn.close()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, current_user: dict = Depends(require_admin)):
    """
    利用者を1件取得する
    
    要件ID: RQ-FT-VIEW-USER-LIST
    設計ID: DS-IF-GET-USER-API-FT-VIEW-USER-LIST
    要件概要: 指定された利用者の情報を取得する（管理者のみ）
    設計概要: ユーザーIDで利用者を検索する
    
    Args:
        user_id: ユーザーID
    
    Returns:
        UserResponse: 利用者情報
    
    Raises:
        HTTPException: 利用者が存在しない場合（404 Not Found）
    """
    db_conn = db_manager.connect()
    try:
        user = user_service.get_user(db_conn, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ユーザーID {user_id} の利用者が見つかりません"
            )
        return user
    finally:
        db_conn.close()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(request: UserCreate, current_user: dict = Depends(require_admin)):
    """
    利用者を登録する
    
    要件ID: RQ-FT-REGISTER-USER
    設計ID: DS-IF-CREATE-USER-API-FT-REGISTER-USER
    要件概要: 利用者を新規登録する（管理者のみ）
    設計概要: ユーザーIDの重複をチェックし、パスワードをハッシュ化して登録する
    
    Args:
        request: 利用者登録リクエスト
    
    Returns:
        UserResponse: 登録された利用者情報
    
    Raises:
        HTTPException: ユーザーIDが重複している場合（400 Bad Request）
    """
    db_conn = db_manager.connect()
    try:
        user = user_service.create_user(
            db_conn,
            request.user_id,
            request.name,
            request.password,
            request.role
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        db_conn.close()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    request: UserUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    利用者を更新する
    
    要件ID: RQ-FT-EDIT-USER
    設計ID: DS-IF-UPDATE-USER-API-FT-EDIT-USER
    要件概要: 利用者情報を編集する（管理者のみ）
    設計概要: ユーザーIDで利用者を検索し、氏名と権限を更新する
    
    Args:
        user_id: ユーザーID
        request: 利用者更新リクエスト
    
    Returns:
        UserResponse: 更新された利用者情報
    
    Raises:
        HTTPException: 利用者が存在しない場合（404 Not Found）
    """
    db_conn = db_manager.connect()
    try:
        user = user_service.update_user(
            db_conn,
            user_id,
            request.name,
            request.password,
            request.role
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    finally:
        db_conn.close()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    """
    利用者を削除する
    
    要件ID: RQ-FT-DELETE-USER
    設計ID: DS-IF-DELETE-USER-API-FT-DELETE-USER
    要件概要: 利用者を削除する（管理者のみ）
    設計概要: ユーザーIDで利用者を検索し、データベースから削除する
    
    Args:
        user_id: ユーザーID
    
    Raises:
        HTTPException: 利用者が存在しない場合（404 Not Found）
    """
    db_conn = db_manager.connect()
    try:
        user_service.delete_user(db_conn, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    finally:
        db_conn.close()

"""
ItemRouter - 備品関連のAPIエンドポイント

要件トレーサビリティ:
  要件ID: RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM, RQ-FT-VIEW-ITEM-LIST
  設計ID: DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM
  要件概要: 備品の登録、編集、削除、貸出、返却、一覧表示を行うAPIを提供する
  設計概要: RESTful APIエンドポイントを提供し、JWT認証と権限チェックを行う
  呼び出し先: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM, DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
  呼び出し元: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN (ApiClient)
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import List
from src.schemas.schemas import ItemResponse, ItemCreate, ItemUpdate, LendRequest
from src.services.item_service import item_service
from src.services.auth_service import auth_service
from src.database.database_manager import db_manager

router = APIRouter(prefix="/api/items", tags=["備品"])


def get_current_user(authorization: str = Header(...)):
    """
    JWT認証を行い、現在のユーザー情報を取得する
    
    要件ID: RQ-NF-ACCESS-CONTROL
    設計ID: DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM
    要件概要: APIリクエスト時にJWT認証を行う
    設計概要: AuthorizationヘッダーからJWTトークンを取得し、検証する
    
    Args:
        authorization: Authorizationヘッダー（"Bearer <token>"）
    
    Returns:
        dict: ユーザー情報（user_id, role）
    
    Raises:
        HTTPException: 認証失敗時（401 Unauthorized）
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが必要です"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証トークンです"
        )
    
    return {"user_id": payload["sub"], "role": payload["role"]}


def require_admin(current_user: dict = Depends(get_current_user)):
    """
    管理者権限をチェックする
    
    要件ID: RQ-NF-ACCESS-CONTROL
    設計ID: DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM
    要件概要: 管理者のみが操作できる機能を制限する
    設計概要: ユーザーの権限が「管理者」であることを確認する
    
    Args:
        current_user: 現在のユーザー情報
    
    Returns:
        dict: ユーザー情報
    
    Raises:
        HTTPException: 権限不足時（403 Forbidden）
    """
    if current_user["role"] != "管理者":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    return current_user


@router.get("", response_model=List[ItemResponse])
def get_items(current_user: dict = Depends(get_current_user)):
    """
    備品一覧を取得する
    
    要件ID: RQ-FT-VIEW-ITEM-LIST
    設計ID: DS-IF-GET-ITEMS-API-FT-VIEW-ITEM-LIST
    要件概要: 備品一覧と貸出状況を表示する
    設計概要: 全備品を取得し、貸出状況を含めて返す
    
    Returns:
        List[ItemResponse]: 備品リスト
    """
    db_conn = db_manager.connect()
    try:
        items = item_service.get_all_items(db_conn)
        return items
    finally:
        db_conn.close()


@router.get("/{asset_number}", response_model=ItemResponse)
def get_item(asset_number: str, current_user: dict = Depends(get_current_user)):
    """
    備品を1件取得する
    
    要件ID: RQ-FT-VIEW-ITEM-LIST
    設計ID: DS-IF-GET-ITEM-API-FT-VIEW-ITEM-LIST
    要件概要: 指定された備品の情報を取得する
    設計概要: 資産管理番号で備品を検索し、貸出状況を含めて返す
    
    Args:
        asset_number: 資産管理番号
    
    Returns:
        ItemResponse: 備品情報
    
    Raises:
        HTTPException: 備品が存在しない場合（404 Not Found）
    """
    db_conn = db_manager.connect()
    try:
        item = item_service.get_item(db_conn, asset_number)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"資産管理番号 {asset_number} の備品が見つかりません"
            )
        return item
    finally:
        db_conn.close()


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(request: ItemCreate, current_user: dict = Depends(require_admin)):
    """
    備品を登録する
    
    要件ID: RQ-FT-REGISTER-ITEM
    設計ID: DS-IF-CREATE-ITEM-API-FT-REGISTER-ITEM
    要件概要: 備品を新規登録する（管理者のみ）
    設計概要: 資産管理番号の重複をチェックし、データベースに登録する
    
    Args:
        request: 備品登録リクエスト
    
    Returns:
        ItemResponse: 登録された備品情報
    
    Raises:
        HTTPException: 資産管理番号が重複している場合（400 Bad Request）
    """
    db_conn = db_manager.connect()
    try:
        item = item_service.create_item(db_conn, request.asset_number, request.name)
        return item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        db_conn.close()


@router.put("/{asset_number}", response_model=ItemResponse)
def update_item(
    asset_number: str,
    request: ItemUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    備品を更新する
    
    要件ID: RQ-FT-EDIT-ITEM
    設計ID: DS-IF-UPDATE-ITEM-API-FT-EDIT-ITEM
    要件概要: 備品情報を編集する（管理者のみ）
    設計概要: 資産管理番号で備品を検索し、名称を更新する
    
    Args:
        asset_number: 資産管理番号
        request: 備品更新リクエスト
    
    Returns:
        ItemResponse: 更新された備品情報
    
    Raises:
        HTTPException: 備品が存在しない場合（404 Not Found）
    """
    db_conn = db_manager.connect()
    try:
        item = item_service.update_item(db_conn, asset_number, request.name)
        return item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    finally:
        db_conn.close()


@router.delete("/{asset_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(asset_number: str, current_user: dict = Depends(require_admin)):
    """
    備品を削除する
    
    要件ID: RQ-FT-DELETE-ITEM
    設計ID: DS-IF-DELETE-ITEM-API-FT-DELETE-ITEM
    要件概要: 備品を削除する（管理者のみ）
    設計概要: 資産管理番号で備品を検索し、データベースから削除する
    
    Args:
        asset_number: 資産管理番号
    
    Raises:
        HTTPException: 備品が存在しない場合（404 Not Found）
    """
    db_conn = db_manager.connect()
    try:
        item_service.delete_item(db_conn, asset_number)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    finally:
        db_conn.close()


@router.post("/{asset_number}/lend", response_model=ItemResponse)
def lend_item(
    asset_number: str,
    request: LendRequest,
    current_user: dict = Depends(require_admin)
):
    """
    備品を貸出する
    
    要件ID: RQ-FT-LEND-ITEM
    設計ID: DS-IF-LEND-ITEM-API-FT-LEND-ITEM
    要件概要: 備品を貸し出す（管理者のみ）
    設計概要: 備品が利用可能かチェックし、借り主を設定して貸出中にする
    
    Args:
        asset_number: 資産管理番号
        request: 貸出リクエスト（借り主）
    
    Returns:
        ItemResponse: 更新された備品情報
    
    Raises:
        HTTPException: 備品が存在しない、または既に貸出中の場合（400 Bad Request）
    """
    db_conn = db_manager.connect()
    try:
        item = item_service.lend_item(db_conn, asset_number, request.borrower)
        return item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        db_conn.close()


@router.post("/{asset_number}/return", response_model=ItemResponse)
def return_item(asset_number: str, current_user: dict = Depends(require_admin)):
    """
    備品を返却する
    
    要件ID: RQ-FT-RETURN-ITEM
    設計ID: DS-IF-RETURN-ITEM-API-FT-RETURN-ITEM
    要件概要: 備品を返却する（管理者のみ）
    設計概要: 備品が貸出中かチェックし、借り主をNULLにして利用可能にする
    
    Args:
        asset_number: 資産管理番号
    
    Returns:
        ItemResponse: 更新された備品情報
    
    Raises:
        HTTPException: 備品が存在しない、または貸出中でない場合（400 Bad Request）
    """
    db_conn = db_manager.connect()
    try:
        item = item_service.return_item(db_conn, asset_number)
        return item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        db_conn.close()

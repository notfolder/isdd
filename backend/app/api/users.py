"""
利用者APIルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-BORROWER, RQ-FT-LOAN-EQUIPMENT
  設計ID: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
  要件概要: 利用者のCRUD操作と貸出先選択用利用者一覧APIエンドポイントを提供する。
  設計概要: FastAPI Router で /api/users の各エンドポイントを定義する。全操作は管理者権限が必要。
  呼び出し先: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
  呼び出し元: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_admin, get_current_user
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserForLoan

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    全利用者一覧を取得する。

    Args:
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用（require_admin Depends）。

    Returns:
        List[UserResponse]: 全利用者のリスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER
      設計ID: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
      要件概要: 管理者が全利用者の一覧を確認できる。
      設計概要: GET /api/users。require_admin で管理者権限を確認してから UserService.list_users() を呼ぶ。
      呼び出し先: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
      呼び出し元: フロントエンド DS-IF-USER-API-FT-MANAGE-BORROWER
    """
    return UserService(db).list_users()


@router.post("", response_model=UserResponse)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    利用者を新規作成する。

    Args:
        data (UserCreate): 作成する利用者データ。
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用。

    Returns:
        UserResponse: 作成された利用者。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER
      設計ID: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
      要件概要: 管理者が新しい利用者を登録できる。
      設計概要: POST /api/users。UserService.create_user() に委譲する。
      呼び出し先: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
      呼び出し元: フロントエンド DS-IF-USER-API-FT-MANAGE-BORROWER
    """
    return UserService(db).create_user(data)


@router.put("/{login_id}", response_model=UserResponse)
def update_user(
    login_id: str,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    利用者情報を更新する。

    Args:
        login_id (str): 更新対象のログインID。
        data (UserUpdate): 更新データ。
        db (Session): DBセッション。
        current_user (User): 操作中の管理者（最後の管理者降格防止チェックに使用）。

    Returns:
        UserResponse: 更新後の利用者。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER
      設計ID: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
      要件概要: 管理者が利用者の表示名・パスワード・ロールを更新できる。
      設計概要: PUT /api/users/{login_id}。current_user.login_id を渡して最後の管理者チェックを行う。
      呼び出し先: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
      呼び出し元: フロントエンド DS-IF-USER-API-FT-MANAGE-BORROWER
    """
    return UserService(db).update_user(login_id, data, current_user.login_id)


@router.delete("/{login_id}")
def delete_user(
    login_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    利用者を削除する。

    Args:
        login_id (str): 削除対象のログインID。
        db (Session): DBセッション。
        current_user (User): 操作中の管理者（自己削除防止チェックに使用）。

    Returns:
        dict: 削除完了メッセージ。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER
      設計ID: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
      要件概要: 管理者が不要な利用者を削除できる。
      設計概要: DELETE /api/users/{login_id}。current_user.login_id を渡して自己削除チェックを行う。
      呼び出し先: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
      呼び出し元: フロントエンド DS-IF-USER-API-FT-MANAGE-BORROWER
    """
    UserService(db).delete_user(login_id, current_user.login_id)
    return {"message": "削除しました"}


@router.get("/for-loan", response_model=List[UserForLoan])
def get_users_for_loan(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """
    貸出先選択用の利用者一覧を取得する。

    Args:
        db (Session): DBセッション。
        _current_user (User): 管理者権限チェック用。

    Returns:
        List[UserForLoan]: ログインIDと表示名のみの利用者リスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOAN-EQUIPMENT
      設計ID: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
      要件概要: 貸出操作時に利用者を選択するためのリストを提供する。
      設計概要: GET /api/users/for-loan。/{login_id} より前に定義してルーティング競合を防ぐ。
      呼び出し先: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
      呼び出し元: フロントエンド DS-IF-USER-API-FT-MANAGE-BORROWER
    """
    return UserService(db).get_users_for_loan()

"""
ユーザー管理APIルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-USERS
  設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
  要件概要: 管理者がユーザーの一覧取得・登録・更新・削除を行うエンドポイントを提供する。
  設計概要: FastAPIルーターでGET/POST/PUT/DELETE /api/users エンドポイントを定義する。全て管理者専用。
  呼び出し先設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
  呼び出し元設計ID: DS-MD-BACKEND-FT-LIST-EQUIPMENT
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> List[UserResponse]:
    """
    全ユーザー一覧を取得する（管理者のみ）。

    Args:
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    Returns:
        List[UserResponse]: 全ユーザーのリスト。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
      要件概要: 管理者がユーザー一覧（氏名・メール・権限）を確認できる。
      設計概要: GET /api/users。管理者権限必須。UserService.list_allに委譲する。
      呼び出し先設計ID: DS-FN-MANAGE-USERS-FT-MANAGE-USERS, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-USER-LIST-VIEW-UI-USER-LIST-SCREEN
    """
    return user_service.list_all(db)


def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    """
    ユーザーを新規登録する（管理者のみ）。

    Args:
        data (UserCreate): 登録データ。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    Returns:
        UserResponse: 登録されたユーザー。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-IF-CREATE-USER-FT-MANAGE-USERS
      要件概要: 管理者が社員アカウントを登録する。メールアドレスは一意。
      設計概要: POST /api/users。管理者権限必須。UserService.createに委譲する。
      呼び出し先設計ID: DS-FN-CREATE-USER-FT-MANAGE-USERS, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-USER-FORM-VIEW-UI-USER-FORM-SCREEN
    """
    return user_service.create(db, data)


def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    """
    ユーザー情報を更新する（管理者のみ）。

    Args:
        user_id (int): 更新対象ユーザーID（パスパラメータ）。
        data (UserUpdate): 更新データ。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    Returns:
        UserResponse: 更新後のユーザー。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-IF-UPDATE-USER-FT-MANAGE-USERS
      要件概要: 管理者が社員アカウント情報を更新する。パスワードは省略時は変更しない。
      設計概要: PUT /api/users/{id}。管理者権限必須。UserService.updateに委譲する。
      呼び出し先設計ID: DS-FN-UPDATE-USER-FT-MANAGE-USERS, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-USER-FORM-VIEW-UI-USER-FORM-SCREEN
    """
    return user_service.update(db, user_id, data)


def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """
    ユーザーを削除する（管理者のみ・貸出中備品がある場合は不可）。

    Args:
        user_id (int): 削除対象ユーザーID（パスパラメータ）。
        db (Session): DBセッション。
        current_user (User): 管理者ユーザー。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-IF-DELETE-USER-FT-MANAGE-USERS
      要件概要: 管理者が社員アカウントを削除する。貸出中備品がある場合は削除できない。
      設計概要: DELETE /api/users/{id}。管理者権限必須。UserService.deleteに委譲する。
      呼び出し先設計ID: DS-FN-DELETE-USER-FT-MANAGE-USERS, DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
      呼び出し元設計ID: DS-CL-USER-LIST-VIEW-UI-USER-LIST-SCREEN
    """
    user_service.delete(db, user_id)


router.get("/", response_model=List[UserResponse])(list_users)
router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)(create_user)
router.put("/{user_id}", response_model=UserResponse)(update_user)
router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)(delete_user)

"""
ユーザーエンドポイント：ユーザーの一覧・登録・更新・削除。

要件トレーサビリティ:
  要件ID: RQ-FT-CREATE-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER
  設計ID: DS-IF-LIST-USERS-FT-DELETE-USER, DS-IF-CREATE-USER-FT-CREATE-USER, DS-IF-UPDATE-USER-FT-EDIT-USER, DS-IF-DELETE-USER-FT-DELETE-USER
  要件概要: 管理者のみユーザーの一覧・登録・更新・削除が可能
  設計概要: GET /api/users(管理者)、POST /api/users(管理者)、PUT /api/users/{id}(管理者)、DELETE /api/users/{id}(管理者)を実装する
  呼び出し先設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import user_service

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    ユーザー一覧を取得する（管理者のみ）。

    Args:
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    Returns:
        List[UserResponse]: ユーザー一覧

    要件トレーサビリティ:
      要件ID: RQ-FT-DELETE-USER
      設計ID: DS-IF-LIST-USERS-FT-DELETE-USER
      要件概要: ユーザー一覧を表示する（管理者のみ）
      設計概要: GET /api/usersで全ユーザーを返す。管理者専用
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return user_service.list_all(db)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    ユーザーを新規登録する（管理者のみ）。

    Args:
        data (UserCreate): 登録データ
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    Returns:
        UserResponse: 登録されたユーザー

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-USER
      設計ID: DS-IF-CREATE-USER-FT-CREATE-USER
      要件概要: 新しいメンバーをシステムに追加し、貸出先として選択可能にする
      設計概要: POST /api/usersで201 Createdを返す。管理者専用。パスワードはハッシュ化
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return user_service.create(db, data)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    ユーザー情報を更新する（管理者のみ）。

    Args:
        user_id (int): ユーザーID
        data (UserUpdate): 更新データ
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    Returns:
        UserResponse: 更新されたユーザー

    要件トレーサビリティ:
      要件ID: RQ-FT-EDIT-USER
      設計ID: DS-IF-UPDATE-USER-FT-EDIT-USER
      要件概要: ユーザー名・ログインID・パスワード・役割の誤りを修正できる
      設計概要: PUT /api/users/{id}で更新する。管理者専用、未存在は404
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    return user_service.update(db, user_id, data)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    ユーザーを削除する（管理者のみ）。

    Args:
        user_id (int): ユーザーID
        current_user (User): 管理者ユーザー
        db (Session): DBセッション

    要件トレーサビリティ:
      要件ID: RQ-FT-DELETE-USER
      設計ID: DS-IF-DELETE-USER-FT-DELETE-USER
      要件概要: 退職者等のアカウントを削除できる。貸出中の備品を持つユーザーは削除不可
      設計概要: DELETE /api/users/{id}で204を返す。貸出中備品ありは409、未存在は404
      呼び出し先設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    user_service.delete(db, user_id)

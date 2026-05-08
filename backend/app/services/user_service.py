"""
ユーザーサービス：ユーザーのCRUD操作と業務制約チェック。

要件トレーサビリティ:
  要件ID: RQ-FT-CREATE-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER
  設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER
  要件概要: ユーザーの登録・参照・更新・削除を行う。貸出中備品を持つユーザーは削除不可
  設計概要: list_all, create(重複login_idは409, パスワードはハッシュ化), update, delete(未返却貸出ありは409)を実装する
  呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY, DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD, DS-FN-CHECK-USER-DELETABLE-FT-DELETE-USER
  呼び出し元設計ID: DS-IF-LIST-USERS-FT-DELETE-USER, DS-IF-CREATE-USER-FT-CREATE-USER
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.loan import Loan
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password


class UserService:
    """
    ユーザーサービスクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-USER
      設計ID: DS-CL-USER-SERVICE-FT-CREATE-USER
      要件概要: ユーザーのCRUD操作を提供する
      設計概要: list_all, create, update, deleteメソッドを実装する
      呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
      呼び出し元設計ID: DS-IF-LIST-USERS-FT-DELETE-USER
    """

    def list_all(self, db: Session) -> List[User]:
        """
        全ユーザー一覧を取得する。

        Args:
            db (Session): DBセッション

        Returns:
            List[User]: ユーザー一覧

        要件トレーサビリティ:
          要件ID: RQ-FT-DELETE-USER
          設計ID: DS-IF-LIST-USERS-FT-DELETE-USER
          要件概要: ユーザー一覧を表示する
          設計概要: 全ユーザーをSELECTして返す
          呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
          呼び出し元設計ID: DS-IF-LIST-USERS-FT-DELETE-USER
        """
        return db.query(User).all()

    def create(self, db: Session, data: UserCreate) -> User:
        """
        ユーザーを新規登録する。

        Args:
            db (Session): DBセッション
            data (UserCreate): 登録データ

        Returns:
            User: 登録されたユーザー

        Raises:
            HTTPException: 重複login_idの場合409

        要件トレーサビリティ:
          要件ID: RQ-FT-CREATE-USER
          設計ID: DS-IF-CREATE-USER-FT-CREATE-USER
          要件概要: 新しいメンバーをシステムに追加し、貸出先として選択可能にする
          設計概要: 重複login_idは409 Conflict。パスワードはbcryptでハッシュ化してから保存
          呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
          呼び出し元設計ID: DS-IF-CREATE-USER-FT-CREATE-USER
        """
        existing = db.query(User).filter(User.login_id == data.login_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="このログインIDは既に使用されています",
            )
        user = User(
            username=data.username,
            login_id=data.login_id,
            password_hash=hash_password(data.password),
            role=data.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, user_id: int, data: UserUpdate) -> User:
        """
        ユーザー情報を更新する。

        Args:
            db (Session): DBセッション
            user_id (int): ユーザーID
            data (UserUpdate): 更新データ

        Returns:
            User: 更新されたユーザー

        Raises:
            HTTPException: ユーザー未存在は404、重複login_idは409

        要件トレーサビリティ:
          要件ID: RQ-FT-EDIT-USER
          設計ID: DS-IF-UPDATE-USER-FT-EDIT-USER
          要件概要: ユーザー名・ログインID・パスワード・役割の誤りを修正できる
          設計概要: 指定IDのユーザーを更新する。未存在は404 Not Found
          呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
          呼び出し元設計ID: DS-IF-UPDATE-USER-FT-EDIT-USER
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )
        if data.login_id is not None:
            existing = db.query(User).filter(
                User.login_id == data.login_id,
                User.id != user_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="このログインIDは既に使用されています",
                )
            user.login_id = data.login_id
        if data.username is not None:
            user.username = data.username
        if data.password is not None:
            user.password_hash = hash_password(data.password)
        if data.role is not None:
            user.role = data.role
        db.commit()
        db.refresh(user)
        return user

    def delete(self, db: Session, user_id: int) -> None:
        """
        ユーザーを削除する。

        Args:
            db (Session): DBセッション
            user_id (int): ユーザーID

        Raises:
            HTTPException: ユーザー未存在は404、未返却貸出ありは409

        要件トレーサビリティ:
          要件ID: RQ-FT-DELETE-USER
          設計ID: DS-FN-CHECK-USER-DELETABLE-FT-DELETE-USER
          要件概要: 退職者等のアカウントを削除できる。貸出中の備品を持つユーザーは削除不可
          設計概要: returned_atがNULLの貸出記録が存在するユーザーは409 Conflictを返す
          呼び出し先設計ID: DS-SC-USER-DT-USER-ENTITY
          呼び出し元設計ID: DS-IF-DELETE-USER-FT-DELETE-USER
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )
        active_loan = db.query(Loan).filter(
            Loan.user_id == user_id,
            Loan.returned_at == None
        ).first()
        if active_loan:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="貸出中の備品を持つユーザーは削除できません",
            )
        db.delete(user)
        db.commit()


user_service = UserService()

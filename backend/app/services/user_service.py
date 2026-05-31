"""
ユーザーサービスモジュール（社員マスターCRUD）。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-USERS
  設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
  要件概要: ユーザーの登録・編集・削除を行う。削除時は貸出中備品があれば削除を禁止する。
  設計概要: UserServiceクラスがユーザーCRUDと削除時貸出中チェックを担う。
  呼び出し先設計ID: DS-SC-USER-DT-ENTITY-USER, DS-SC-LENDING-DT-ENTITY-LENDING
  呼び出し元設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.lending import LendingRecord
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import hash_password


class UserService:
    """
    ユーザービジネスロジックサービスクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-USERS
      設計ID: DS-CL-USER-SERVICE-FT-MANAGE-USERS
      要件概要: ユーザーCRUD・削除時貸出中チェックを担う。
      設計概要: list_all/create/update/deleteの4メソッドで構成。パスワードはbcryptハッシュ化して保存。
      呼び出し先設計ID: DS-SC-USER-DT-ENTITY-USER, DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH
      呼び出し元設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
    """

    def list_all(self, db: Session) -> List[UserResponse]:
        """
        全ユーザーを一覧取得する。

        Args:
            db (Session): DBセッション。

        Returns:
            List[UserResponse]: 全ユーザーのレスポンスリスト（パスワード除外）。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-USERS
          設計ID: DS-FN-MANAGE-USERS-FT-MANAGE-USERS
          要件概要: ユーザー一覧で氏名・メールアドレス・権限を管理者が確認できる。
          設計概要: usersテーブルを全件取得しUserResponseに変換して返す。
          呼び出し先設計ID: DS-SC-USER-DT-ENTITY-USER
          呼び出し元設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
        """
        users = db.query(User).all()
        return [UserResponse.model_validate(u) for u in users]

    def create(self, db: Session, data: UserCreate) -> UserResponse:
        """
        ユーザーを新規登録する。

        Args:
            db (Session): DBセッション。
            data (UserCreate): 登録データ。

        Returns:
            UserResponse: 登録されたユーザーレスポンス。

        Raises:
            HTTPException: 409 メールアドレス重複の場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-USERS
          設計ID: DS-FN-CREATE-USER-FT-MANAGE-USERS
          要件概要: 氏名・メール・パスワード・権限を受け取りユーザーを登録する。パスワードはハッシュ化して保存。
          設計概要: メールアドレス重複チェック後にINSERT。パスワードはbcryptでハッシュ化。重複時は409。
          呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH, DS-SC-USER-DT-ENTITY-USER
          呼び出し元設計ID: DS-IF-CREATE-USER-FT-MANAGE-USERS
        """
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="このメールアドレスは既に使用されています",
            )
        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    def update(self, db: Session, user_id: int, data: UserUpdate) -> UserResponse:
        """
        ユーザー情報を更新する。

        Args:
            db (Session): DBセッション。
            user_id (int): 更新対象のユーザーID。
            data (UserUpdate): 更新データ。

        Returns:
            UserResponse: 更新後のユーザーレスポンス。

        Raises:
            HTTPException: 404 ユーザー不在、409 メール重複の場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-USERS
          設計ID: DS-FN-UPDATE-USER-FT-MANAGE-USERS
          要件概要: 氏名・メール・パスワード・権限を更新する。パスワードはNoneの場合は変更しない。
          設計概要: IDでUserを検索し各フィールドを更新。passwordが指定された場合はハッシュ化して更新。
          呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH, DS-SC-USER-DT-ENTITY-USER
          呼び出し元設計ID: DS-IF-UPDATE-USER-FT-MANAGE-USERS
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="該当するユーザーが見つかりません")
        if data.email != user.email:
            existing = db.query(User).filter(User.email == data.email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="このメールアドレスは既に使用されています",
                )
        user.name = data.name
        user.email = data.email
        user.role = data.role
        if data.password:
            user.password_hash = hash_password(data.password)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    def delete(self, db: Session, user_id: int) -> None:
        """
        ユーザーを削除する（貸出中備品がある場合は削除不可）。

        Args:
            db (Session): DBセッション。
            user_id (int): 削除対象のユーザーID。

        Raises:
            HTTPException: 404 ユーザー不在、409 貸出中備品あり。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-USERS
          設計ID: DS-FN-DELETE-USER-FT-MANAGE-USERS
          要件概要: ユーザーを削除する。貸出中備品がある場合は削除を禁止する（先に返却が必要）。
          設計概要: lending_recordsに当該ユーザーの貸出記録が存在する場合は409を返す。なければDELETE。
          呼び出し先設計ID: DS-SC-USER-DT-ENTITY-USER, DS-SC-LENDING-DT-ENTITY-LENDING
          呼び出し元設計ID: DS-IF-DELETE-USER-FT-MANAGE-USERS
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="該当するユーザーが見つかりません")
        active_lending = db.query(LendingRecord).filter(LendingRecord.user_id == user_id).first()
        if active_lending:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="この社員は備品を貸出中のため削除できません",
            )
        db.delete(user)
        db.commit()


user_service = UserService()

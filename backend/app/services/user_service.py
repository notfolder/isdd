"""
利用者サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-BORROWER, RQ-OP-INITIAL-ADMIN-ENV, RQ-NF-PASSWORD-HASH
  設計ID: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
  要件概要: 利用者のCRUD操作と初期管理者作成を提供する。最後の管理者の削除・降格と貸出中利用者の削除を防ぐ。
  設計概要: UserRepository と LoanStateRepository を組み合わせて利用者管理のビジネスロジックを実装する。
  呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
  呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
"""
from typing import List
import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.loan_state import LoanStateRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserForLoan
from app.core.config import settings


class UserService:
    """
    利用者管理のビジネスロジックを担うサービスクラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-BORROWER, RQ-OP-INITIAL-ADMIN-ENV
      設計ID: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
      要件概要: 利用者のCRUD操作と初期管理者作成、制約チェックを提供する。
      設計概要: UserRepository と LoanStateRepository をコンポーズしてビジネスルールを適用する。
      呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
      呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.loan_repo = LoanStateRepository(db)

    def initialize_admin(self) -> None:
        """
        初期管理者を作成する。利用者テーブルが空の場合のみ実行する。

        要件トレーサビリティ:
          要件ID: RQ-OP-INITIAL-ADMIN-ENV, RQ-NF-PASSWORD-HASH
          設計ID: DS-FN-INIT-ADMIN-OP-INITIAL-ADMIN-ENV
          要件概要: 起動時にDBが空の場合のみ、環境変数で指定した初期管理者を作成する。
          設計概要: count_all() == 0 の場合のみ bcrypt でパスワードをハッシュ化してadminユーザーを作成する。
          呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          呼び出し元: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT
        """
        if self.user_repo.count_all() > 0:
            return
        password_hash = bcrypt.hashpw(
            settings.initial_admin_password.encode(), bcrypt.gensalt()
        ).decode()
        admin = User(
            login_id=settings.initial_admin_login_id,
            display_name="管理者",
            password_hash=password_hash,
            role="admin",
        )
        self.user_repo.create(admin)
        self.db.commit()

    def list_users(self) -> List[UserResponse]:
        """
        全利用者一覧を取得する。

        Returns:
            List[UserResponse]: 全利用者のレスポンスリスト。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER
          設計ID: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
          要件概要: 管理者が全利用者の一覧を確認できる。
          設計概要: UserRepository.find_all() の結果を UserResponse に変換して返す。
          呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
        """
        users = self.user_repo.find_all()
        return [UserResponse.model_validate(u) for u in users]

    def create_user(self, data: UserCreate) -> UserResponse:
        """
        利用者を新規作成する。

        Args:
            data (UserCreate): 作成する利用者データ。

        Returns:
            UserResponse: 作成された利用者のレスポンス。

        Raises:
            HTTPException: 400 - ログインIDが既に使用されている場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER, RQ-NF-PASSWORD-HASH
          設計ID: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
          要件概要: 管理者が新しい利用者を登録できる。ログインIDの重複は許可しない。パスワードはハッシュ化する。
          設計概要: login_id の重複チェック後、bcrypt でパスワードをハッシュ化してユーザーを作成する。
          呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
        """
        if self.user_repo.find_by_login_id(data.login_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このログインIDは既に使用されています",
            )
        password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        user = User(
            login_id=data.login_id,
            display_name=data.display_name,
            password_hash=password_hash,
            role=data.role,
        )
        self.user_repo.create(user)
        self.db.commit()
        return UserResponse.model_validate(user)

    def update_user(self, login_id: str, data: UserUpdate, current_user_login_id: str) -> UserResponse:
        """
        利用者情報を更新する。

        Args:
            login_id (str): 更新対象のログインID。
            data (UserUpdate): 更新データ（display_name・password・role のいずれか）。
            current_user_login_id (str): 操作中の管理者のログインID（最後の管理者降格防止に使用）。

        Returns:
            UserResponse: 更新後の利用者レスポンス。

        Raises:
            HTTPException: 404 - 利用者が見つからない場合。
            HTTPException: 400 - 最後の管理者のロールを変更しようとした場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER, RQ-NF-ROLE-ACCESS
          設計ID: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
          要件概要: 管理者が利用者の表示名・パスワード・ロールを更新できる。最後の管理者の降格は禁止する。
          設計概要: 管理者数チェック後、各フィールドを選択的に更新する。パスワードは bcrypt で再ハッシュする。
          呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
        """
        user = self.user_repo.find_by_login_id(login_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="利用者が見つかりません")
        if data.role is not None and data.role != user.role:
            if user.role == "admin" and self.user_repo.count_admins() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="最後の管理者の権限は変更できません",
                )
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.password is not None:
            user.password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        if data.role is not None:
            user.role = data.role
        self.user_repo.update(user)
        self.db.commit()
        return UserResponse.model_validate(user)

    def delete_user(self, login_id: str, current_user_login_id: str) -> None:
        """
        利用者を削除する。

        Args:
            login_id (str): 削除対象のログインID。
            current_user_login_id (str): 操作中の管理者のログインID（自己削除防止に使用）。

        Raises:
            HTTPException: 404 - 利用者が見つからない場合。
            HTTPException: 400 - 自己削除・最後の管理者削除・貸出中利用者削除を試みた場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER, RQ-NF-ROLE-ACCESS
          設計ID: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
          要件概要: 管理者が利用者を削除できる。自己削除・最後の管理者削除・貸出中利用者の削除は禁止する。
          設計概要: 3段階の制約チェック（自己・最後の管理者・貸出中）を順次実行してから削除する。
          呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
          呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
        """
        user = self.user_repo.find_by_login_id(login_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="利用者が見つかりません")
        if login_id == current_user_login_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="自分自身は削除できません",
            )
        if user.role == "admin" and self.user_repo.count_admins() <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="最後の管理者は削除できません",
            )
        if self.loan_repo.exists_by_user_login_id(login_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="貸出中の備品がある利用者は削除できません",
            )
        self.user_repo.delete(user)
        self.db.commit()

    def get_users_for_loan(self) -> List[UserForLoan]:
        """
        貸出先選択用の利用者一覧を取得する。

        Returns:
            List[UserForLoan]: 全利用者のログインIDと表示名のリスト。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOAN-EQUIPMENT
          設計ID: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
          要件概要: 貸出操作時に利用者を選択するためのリストを提供する。
          設計概要: UserRepository.find_all() の結果を UserForLoan（login_id と display_name のみ）に変換する。
          呼び出し先: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
        """
        users = self.user_repo.find_all()
        return [UserForLoan.model_validate(u) for u in users]

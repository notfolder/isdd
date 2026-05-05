"""
利用者リポジトリモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-USER-ENTITY, RQ-FT-MANAGE-BORROWER
  設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
  要件概要: 利用者エンティティの永続化操作（検索・カウント・作成・更新・削除）を提供する。
  設計概要: SQLAlchemy Session を受け取り、User モデルに対するCRUD操作をカプセル化する。
  呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
  呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER, DS-CL-AUTH-SERVICE-FT-LOGIN
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    """
    利用者エンティティのDB操作クラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-DT-USER-ENTITY
      設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
      要件概要: 利用者エンティティのCRUD操作をDBレイヤーとして提供する。
      設計概要: Service 層から受け取った db セッションで User テーブルを操作する。
      呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
      呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
    """

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> List[User]:
        """
        全利用者を取得する。

        Returns:
            List[User]: 全利用者のリスト。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER
          設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          要件概要: 管理者が全利用者の一覧を確認できる。
          設計概要: user テーブルの全レコードを返す。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
        """
        return self.db.query(User).all()

    def find_by_login_id(self, login_id: str) -> Optional[User]:
        """
        ログインIDで利用者を取得する。

        Args:
            login_id (str): 検索するログインID。

        Returns:
            Optional[User]: 見つかった利用者、または None。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN, RQ-FT-MANAGE-BORROWER
          設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          要件概要: ログイン認証および利用者の存在確認に使用する。
          設計概要: login_id を主キーとして1件検索する。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER, DS-CL-AUTH-SERVICE-FT-LOGIN
        """
        return self.db.query(User).filter(User.login_id == login_id).first()

    def count_admins(self) -> int:
        """
        管理者ロールの利用者数を返す。

        Returns:
            int: 管理者ロールの利用者数。

        要件トレーサビリティ:
          要件ID: RQ-NF-ROLE-ACCESS, RQ-FT-MANAGE-BORROWER
          設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          要件概要: 最後の管理者の削除・降格を防ぐために管理者数を確認する。
          設計概要: role == 'admin' でフィルタして件数を返す。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
        """
        return self.db.query(User).filter(User.role == "admin").count()

    def count_all(self) -> int:
        """
        全利用者数を返す。

        Returns:
            int: 全利用者数。

        要件トレーサビリティ:
          要件ID: RQ-OP-INITIAL-ADMIN-ENV
          設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          要件概要: 起動時に利用者が0件の場合のみ初期管理者を作成する判定に使用する。
          設計概要: user テーブルの全件数を返す。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
        """
        return self.db.query(User).count()

    def create(self, user: User) -> User:
        """
        利用者を新規作成する。

        Args:
            user (User): 作成する利用者モデル。

        Returns:
            User: 作成された利用者モデル。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER, RQ-OP-INITIAL-ADMIN-ENV
          設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          要件概要: 管理者が新しい利用者を登録できる。初期管理者作成にも使用する。
          設計概要: db.add + flush でセッションに追加する（commit は Service 層が行う）。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
        """
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User) -> User:
        """
        利用者情報を更新する。

        Args:
            user (User): 更新済み利用者モデル。

        Returns:
            User: 更新された利用者モデル。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER
          設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          要件概要: 管理者が利用者の表示名・パスワード・ロールを更新できる。
          設計概要: セッション追跡済みオブジェクトを flush する。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
        """
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        """
        利用者を削除する。

        Args:
            user (User): 削除する利用者モデル。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER
          設計ID: DS-CL-USER-REPO-DT-BORROWER-ENTITY
          要件概要: 管理者が不要な利用者を削除できる。
          設計概要: db.delete + flush で削除をセッションに反映する。
          呼び出し先: DS-MD-USER-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
        """
        self.db.delete(user)
        self.db.flush()

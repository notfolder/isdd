"""
初期管理者アカウントのシードデータ投入。

要件トレーサビリティ:
  要件ID: RQ-FT-CREATE-USER
  設計ID: DS-FN-SEED-INITIAL-USER-FT-CREATE-USER
  要件概要: 初期管理者アカウントをシステム初期化時に1件登録する
  設計概要: login_idがadminのユーザーが未存在の場合のみINSERTする。2回目以降の起動で重複登録しない
  呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password


def seed_initial_admin(db: Session) -> None:
    """
    初期管理者アカウントを投入する。

    Args:
        db (Session): DBセッション

    要件トレーサビリティ:
      要件ID: RQ-FT-CREATE-USER
      設計ID: DS-FN-SEED-INITIAL-USER-FT-CREATE-USER
      要件概要: 初期管理者アカウントをシステム初期化時に1件登録する
      設計概要: login_idがadminのユーザーが未存在の場合のみINSERTする
      呼び出し先設計ID: DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """
    existing = db.query(User).filter(User.login_id == "admin").first()
    if existing is None:
        admin_user = User(
            username="システム管理者",
            login_id="admin",
            password_hash=hash_password("admin"),
            role="admin",
        )
        db.add(admin_user)
        db.commit()

"""
環境変数設定モジュール。

要件トレーサビリティ:
  要件ID: RQ-OP-INITIAL-ADMIN-ENV, RQ-NF-PASSWORD-HASH
  設計ID: DS-FN-AUTH-JWT-FT-LOGIN
  要件概要: JWT秘密鍵・初期管理者ID/PWを環境変数から読み込む。
  設計概要: pydantic_settings の BaseSettings で環境変数をバリデーション付きで読み込む。
  呼び出し先: なし
  呼び出し元: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    アプリ設定クラス。環境変数から設定値を読み込む。

    要件トレーサビリティ:
      要件ID: RQ-OP-INITIAL-ADMIN-ENV, RQ-NF-PASSWORD-HASH
      設計ID: DS-FN-AUTH-JWT-FT-LOGIN
      要件概要: JWT_SECRET_KEY・INITIAL_ADMIN_LOGIN_ID・INITIAL_ADMIN_PASSWORD を環境変数で設定可能にする。
      設計概要: pydantic_settings で型安全に環境変数を読み込む。デフォルト値は開発用のみ。
      呼び出し先: なし
      呼び出し元: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
    """
    jwt_secret_key: str = "dev-secret-key"
    initial_admin_login_id: str = "admin"
    initial_admin_password: str = "changeme"

    class Config:
        env_file = ".env"


settings = Settings()

"""
AuthService単体テスト。

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  要件概要: ログイン認証のビジネスロジックを検証する
  設計概要: test_login_success, test_login_fail_wrong_password, test_login_fail_user_not_foundを実装する
  呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.services.auth_service import AuthService
from app.core.security import hash_password


def create_test_user(db):
    """テスト用ユーザーを作成するヘルパー関数。"""
    user = User(
        username="テストユーザー",
        login_id="testuser",
        password_hash=hash_password("testpass"),
        role="admin",
    )
    db.add(user)
    db.commit()
    return user


class TestAuthService:
    """
    AuthService単体テストクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-LOGIN
      設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      要件概要: ログイン認証の正常系・異常系を検証する
      設計概要: login()メソッドのテストケースを実装する
      呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """

    def test_login_success(self, db):
        """
        正しい認証情報でJWTトークンが返ることを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN
          設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          要件概要: 正しいログインIDとパスワードでJWTトークンが返ること
          設計概要: login()が{'access_token': str, 'role': str}を返すことを確認する
          呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        create_test_user(db)
        service = AuthService()
        result = service.login("testuser", "testpass", db)
        assert "access_token" in result
        assert result["role"] == "admin"

    def test_login_fail_wrong_password(self, db):
        """
        誤ったパスワードで401例外が発生することを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN
          設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          要件概要: 誤ったパスワードでエラーメッセージが表示され遷移しない
          設計概要: 誤パスワードでHTTPException(401)が発生することを確認する
          呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        create_test_user(db)
        service = AuthService()
        with pytest.raises(HTTPException) as exc_info:
            service.login("testuser", "wrongpass", db)
        assert exc_info.value.status_code == 401

    def test_login_fail_user_not_found(self, db):
        """
        存在しないログインIDで401例外が発生することを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOGIN
          設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          要件概要: 存在しないユーザーでエラーになること
          設計概要: 存在しないlogin_idでHTTPException(401)が発生することを確認する
          呼び出し先設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        service = AuthService()
        with pytest.raises(HTTPException) as exc_info:
            service.login("nonexistent", "anypass", db)
        assert exc_info.value.status_code == 401

"""
AuthService - 認証処理とパスワードハッシュ化を管理するクラス

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH
  設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
  要件概要: ユーザーIDとパスワードでログインし、パスワードはハッシュ化して保存する
  設計概要: bcryptでパスワードをハッシュ化し、JWTトークンを発行・検証する
  呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
  呼び出し元: DS-CL-AUTH-ROUTER-FT-LOGIN
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os


class AuthService:
    """
    認証処理とパスワードハッシュ化を管理するクラス
    
    要件ID: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH
    設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
    """
    
    def __init__(self):
        """
        AuthServiceを初期化する
        
        要件ID: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH
        設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
        """
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_hours = 24
    
    def hash_password(self, password: str) -> str:
        """
        パスワードをハッシュ化する
        
        Args:
            password (str): 平文パスワード
        
        Returns:
            str: ハッシュ化されたパスワード
        
        要件ID: RQ-NF-PASSWORD-HASH
        設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
        要件概要: パスワードは平文で保存せず、ハッシュ化して保存する
        設計概要: bcryptを使用してパスワードをハッシュ化する
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        パスワードを検証する
        
        Args:
            plain_password (str): 平文パスワード
            hashed_password (str): ハッシュ化されたパスワード
        
        Returns:
            bool: パスワードが一致する場合True
        
        要件ID: RQ-FT-LOGIN
        設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
        要件概要: ログイン時にパスワードを検証する
        設計概要: bcryptを使用してパスワードを検証する
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def authenticate(self, db_conn, user_id: str, password: str) -> Optional[Dict]:
        """
        ユーザー認証を行う
        
        Args:
            db_conn: データベース接続
            user_id (str): ユーザーID
            password (str): パスワード
        
        Returns:
            Optional[Dict]: 認証成功時はユーザー情報、失敗時はNone
        
        要件ID: RQ-FT-LOGIN
        設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
        要件概要: ユーザーIDとパスワードでログインする
        設計概要: データベースからユーザー情報を取得し、パスワードを検証する
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT user_id, name, password_hash, role FROM users WHERE user_id = ?",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user is None:
            return None
        
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        return {
            "user_id": user["user_id"],
            "name": user["name"],
            "role": user["role"]
        }
    
    def create_token(self, user_id: str, role: str) -> str:
        """
        JWTトークンを発行する
        
        Args:
            user_id (str): ユーザーID
            role (str): 権限
        
        Returns:
            str: JWTトークン
        
        要件ID: RQ-FT-LOGIN
        設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
        要件概要: ログイン成功時にJWTトークンを発行する
        設計概要: ユーザーIDと権限を含むJWTトークンを発行する（有効期限: 24時間）
        """
        expire = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        JWTトークンを検証する
        
        Args:
            token (str): JWTトークン
        
        Returns:
            Optional[Dict]: トークンが有効な場合はペイロード、無効な場合はNone
        
        要件ID: RQ-FT-LOGIN, RQ-NF-ACCESS-CONTROL
        設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
        要件概要: APIリクエスト時にJWTトークンを検証し、権限を確認する
        設計概要: JWTトークンを検証し、ユーザーIDと権限を取得する
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None


# シングルトンインスタンス
auth_service = AuthService()

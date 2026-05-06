"""
AuthRouter - 認証関連のAPIエンドポイント

要件トレーサビリティ:
  要件ID: RQ-FT-LOGIN
  設計ID: DS-CL-AUTH-ROUTER-FT-LOGIN
  要件概要: ユーザーIDとパスワードでログインする
  設計概要: POST /api/auth/login エンドポイントを提供し、JWTトークンを発行する
  呼び出し先: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
  呼び出し元: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN (ApiClient)
"""

from fastapi import APIRouter, HTTPException, status
from src.schemas.schemas import LoginRequest, LoginResponse
from src.services.auth_service import auth_service
from src.database.database_manager import db_manager

router = APIRouter(prefix="/api/auth", tags=["認証"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    ログイン処理
    
    要件ID: RQ-FT-LOGIN
    設計ID: DS-IF-LOGIN-API-FT-LOGIN
    要件概要: ユーザーIDとパスワードでログインし、JWTトークンを取得する
    設計概要: ユーザー認証を行い、成功時はJWTトークンとユーザー情報を返す
    呼び出し先: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
    
    Args:
        request: ログインリクエスト（ユーザーID、パスワード）
    
    Returns:
        LoginResponse: JWTトークン、ユーザーID、権限
    
    Raises:
        HTTPException: ログイン失敗時（401 Unauthorized）
    """
    db_conn = db_manager.connect()
    
    try:
        user = auth_service.authenticate(db_conn, request.user_id, request.password)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザーIDまたはパスワードが正しくありません"
            )
        
        token = auth_service.create_token(user["user_id"], user["role"])
        
        return LoginResponse(
            access_token=token,
            user_id=user["user_id"],
            role=user["role"]
        )
    finally:
        db_conn.close()

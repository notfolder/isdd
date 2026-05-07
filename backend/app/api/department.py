"""
部署名取得APIルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-DEPT-NAME-API, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
  要件概要: ログインIDに対応する部署名を返す API エンドポイントを提供する。
  設計概要: GET /api/department/by-login-id。ログイン済みユーザーのみ呼び出し可。未認証は 401。
  呼び出し先: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
  呼び出し元: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT
"""
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user
from app.core.external_department import get_department_client
from app.models.user import User
from app.services.department_service import DepartmentService
from app.schemas.department import DeptNameResponse

router = APIRouter(prefix="/api/department", tags=["department"])


@router.get("/by-login-id", response_model=DeptNameResponse)
def get_dept_name(
    login_id: str = Query(..., description="内部利用者のログインID"),
    _current_user: User = Depends(get_current_user),
    client=Depends(get_department_client),
):
    """
    ログインIDに対応する部署名を返す。

    Args:
        login_id (str): 内部利用者のログインID（クエリパラメータ、必須）。
        _current_user (User): ログイン確認用（未認証は 401）。
        client: DI ファクトリから注入される部署クライアント。

    Returns:
        DeptNameResponse: 部署名。照合失敗・接続失敗時は "不明"。

    要件トレーサビリティ:
      要件ID: RQ-FT-DEPT-NAME-API, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API
      要件概要: GET /api/department/by-login-id。ログイン済みで 200、未認証で 401。
      設計概要: DepartmentService に委譲し、None・例外は "不明" に変換して返す。
      呼び出し先: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
      呼び出し元: フロントエンド DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
    """
    service = DepartmentService(client)
    department_name = service.get_department_name(login_id)
    return DeptNameResponse(department_name=department_name)

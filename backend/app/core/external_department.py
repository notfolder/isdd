"""
外部部署クライアント DI ファクトリモジュール。

要件トレーサビリティ:
  要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
  要件概要: 環境変数 MOCK_EXTERNAL_DB に応じて MockDepartmentClient または RealDepartmentClient を返す。
  設計概要: FastAPI Depends で利用できるファクトリ関数。MOCK_EXTERNAL_DB=true 時は Mock、それ以外は Real を返す。
  呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER, DS-CL-MOCK-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
  呼び出し元: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
"""
import os


def get_department_client():
    """
    MOCK_EXTERNAL_DB 環境変数に応じてクライアントを返す FastAPI Depends ファクトリ。

    Returns:
        MockDepartmentClient | RealDepartmentClient: 環境変数に応じたクライアントインスタンス。

    要件トレーサビリティ:
      要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER
      設計ID: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
      要件概要: MOCK_EXTERNAL_DB=true の場合は外部DB不要のモックを使用する。それ以外は実 Neon PostgreSQL に接続する。
      設計概要: os.environ で MOCK_EXTERNAL_DB を読み込み、"true" なら MockDepartmentClient、それ以外は RealDepartmentClient を返す。
      呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER, DS-CL-MOCK-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
      呼び出し元: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
    """
    if os.environ.get("MOCK_EXTERNAL_DB", "false").lower() == "true":
        from mock.mock_department_client import MockDepartmentClient
        return MockDepartmentClient()
    else:
        from src.department_client import RealDepartmentClient
        return RealDepartmentClient()

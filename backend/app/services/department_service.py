"""
部署サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-EX-FETCH-DEPARTMENT-MASTER
  設計ID: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
  要件概要: ログインIDに対応する部署名を取得する。外部DB接続失敗・照合失敗時は "不明" を返す。
  設計概要: クライアント（RealDepartmentClient / MockDepartmentClient）を注入して部署名を取得し、
             None または例外発生時は "不明" に変換する。
  呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER, DS-CL-MOCK-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
  呼び出し元: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
"""


class DepartmentService:
    """
    部署名取得ビジネスロジッククラス。

    Args:
        client: fetch_department_name_by_login_id(login_id) メソッドを持つクライアント。

    要件トレーサビリティ:
      要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-EX-FETCH-DEPARTMENT-MASTER
      設計ID: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
      要件概要: 外部DBから部署名を取得し、失敗時は "不明" を返す。
      設計概要: クライアントを注入して get_department_name で None・例外を "不明" に吸収する。
      呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
      呼び出し元: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
    """

    def __init__(self, client):
        self._client = client

    def get_department_name(self, login_id: str) -> str:
        """
        ログインIDに対応する部署名を取得する。

        Args:
            login_id (str): 内部利用者のログインID。

        Returns:
            str: 部署名。照合失敗・接続失敗・例外時は "不明" を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-EX-FETCH-DEPARTMENT-MASTER
          設計ID: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
          要件概要: 外部DB接続失敗時は "不明" を返し、他の操作は継続可能とする。
          設計概要: _client.fetch_department_name_by_login_id を呼び出す。None・例外は "不明" に変換する。
          呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
          呼び出し元: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
        """
        try:
            result = self._client.fetch_department_name_by_login_id(login_id)
            if result is None:
                return "不明"
            return result
        except Exception:
            return "不明"

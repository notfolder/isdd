"""
部署スキーマモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-DEPT-NAME-API, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API
  要件概要: 部署名取得APIのレスポンスデータ構造を定義する。
  設計概要: Pydantic BaseModel で部署名レスポンスを型安全に定義する。
  呼び出し先: なし
  呼び出し元: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API, DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
"""
from pydantic import BaseModel


class DeptNameResponse(BaseModel):
    """
    部署名取得レスポンススキーマ。

    Attributes:
        department_name (str): 部署名。照合失敗・外部DB接続失敗時は "不明"。

    要件トレーサビリティ:
      要件ID: RQ-FT-DEPT-NAME-API
      設計ID: DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API
      要件概要: ログインIDに対応する部署名を返す。不明な場合は "不明" を返す。
      設計概要: department_name フィールドのみを持つシンプルなレスポンス。
      呼び出し先: なし
      呼び出し元: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
    """

    department_name: str

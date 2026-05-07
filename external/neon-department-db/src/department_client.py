"""
Neon PostgreSQL 部署マスタ 薄いラッパークライアント。

要件トレーサビリティ:
  要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
  要件概要: 外部DB（demo_departments・demo_users）から部署情報を取得する。SELECT のみ。
  設計概要: SQLAlchemy 2.0 + psycopg2-binary で Neon PostgreSQL に接続する薄いラッパー。
             NullPool を使用し PgBouncer との二重プーリングを防止する。
             モジュールレベル関数（get_external_db_engine / fetch_department_name_by_login_id）と
             MockDepartmentClient と同一インターフェースを持つ RealDepartmentClient クラスを提供する。
  呼び出し先: なし
  呼び出し元: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
"""
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from typing import Optional
import os


def get_external_db_engine():
    """
    外部DB用 SQLAlchemy エンジンを生成する。

    要件トレーサビリティ:
      要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-NF-EXTERNAL-DB-TIMEOUT
      設計ID: DS-FN-GET-EXTERNAL-ENGINE-EX-FETCH-DEPARTMENT-MASTER (仮ID)
      要件概要: EXTERNAL_DB_URL 環境変数から接続文字列を読み込み、接続タイムアウト5秒以内でエンジンを生成する。
      設計概要: NullPool で PgBouncer 二重プーリングを防止。pool_pre_ping=True でコールドスタート対策。
      呼び出し先: なし
      呼び出し元: DS-FN-FETCH-DEPT-NAME-FT-FETCH-DEPT-BY-LOGIN-ID (仮ID)
    """
    url = os.environ.get("EXTERNAL_DB_URL")
    if not url:
        raise ValueError("EXTERNAL_DB_URL が設定されていません")
    return create_engine(
        url,
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


def fetch_department_name_by_login_id(engine, login_id: str) -> Optional[str]:
    """
    ログインIDに対応する部署名を外部DBから取得する。

    Args:
        engine: SQLAlchemy エンジン（get_external_db_engine() で生成）
        login_id: 内部利用者のログインID

    Returns:
        部署名（str）。demo_users に一致するレコードがない場合は None を返す。

    要件トレーサビリティ:
      要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-EX-FETCH-DEPARTMENT-MASTER
      設計ID: DS-FN-FETCH-DEPT-NAME-FT-FETCH-DEPT-BY-LOGIN-ID (仮ID)
      要件概要: login_id = demo_users.user_id で照合し、dept.department_name を返す。不一致は None。
      設計概要: demo_users JOIN demo_departments の単一 SELECT クエリで取得する。
      呼び出し先: なし
      呼び出し元: DS-CL-DEPT-SERVICE-EX-FETCH-DEPARTMENT-MASTER (仮ID)
    """
    query = text(
        "SELECT d.department_name "
        "FROM demo_users u "
        "JOIN demo_departments d ON u.department_id = d.department_id "
        "WHERE u.user_id = :login_id"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"login_id": login_id})
        row = result.fetchone()
        return row[0] if row else None


class RealDepartmentClient:
    """
    本番用外部DBクライアント。MockDepartmentClient と同一インターフェースを提供する。

    要件トレーサビリティ:
      要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
      設計ID: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
      要件概要: 本番環境で Neon PostgreSQL に接続して部署名を取得する。
      設計概要: get_external_db_engine() でエンジンを生成して保持し、
                fetch_department_name_by_login_id モジュール関数を呼び出す。
      呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER（get_external_db_engine）
      呼び出し元: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
    """

    def __init__(self):
        """
        エンジンを生成して保持する。

        要件トレーサビリティ:
          要件ID: RQ-EX-FETCH-DEPARTMENT-MASTER, RQ-NF-EXTERNAL-DB-TIMEOUT
          設計ID: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
          要件概要: EXTERNAL_DB_URL から SQLAlchemy エンジンを生成する。タイムアウト5秒。
          設計概要: get_external_db_engine() でエンジンを生成して self._engine に保持する。
          呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER（get_external_db_engine）
          呼び出し元: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
        """
        self._engine = get_external_db_engine()

    def fetch_department_name_by_login_id(self, login_id: str) -> Optional[str]:
        """
        ログインIDに対応する部署名を外部DBから取得する。

        Args:
            login_id (str): 内部利用者のログインID。

        Returns:
            Optional[str]: 部署名。照合失敗時は None を返す。

        要件トレーサビリティ:
          要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-EX-FETCH-DEPARTMENT-MASTER
          設計ID: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER
          要件概要: login_id で demo_users を照合し department_name を返す。不一致は None。
          設計概要: モジュールレベルの fetch_department_name_by_login_id(self._engine, login_id) を呼び出す。
          呼び出し先: DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER（fetch_department_name_by_login_id 関数）
          呼び出し元: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
        """
        return fetch_department_name_by_login_id(self._engine, login_id)


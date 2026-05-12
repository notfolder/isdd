"""外部部署DBから部署名を取得する読み取り専用ラッパー。

要件トレーサビリティ:
  要件ID: RQ-EX-CONNECT-EXTERNAL-DEPARTMENT-DB
  設計ID: DS-IF-CONNECT-EXTERNAL-DEPARTMENT-DB-EX-CONNECT-EXTERNAL-DEPARTMENT-DB
  要件概要: login_id=user_id の対応で外部DBから部署名を取得する。
  設計概要: external/neon-postgres/src を唯一の接続窓口とし、アプリ本体から直接接続を禁止する。
  呼び出し先設計ID: DS-MD-READ-ONLY-EXTERNAL-DEPARTMENT-DB-EX-READ-ONLY-EXTERNAL-DEPARTMENT-DB
  呼び出し元設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
"""

from __future__ import annotations

import os
import importlib.util
from pathlib import Path

try:
    import psycopg
except Exception:  # pragma: no cover - 実行環境依存
    psycopg = None


SRC_DIR = Path(__file__).resolve().parent
MOCK_FILE_PATH = SRC_DIR.parent / "mock" / "psycopg_mock.py"


SELECT_DEPARTMENT_NAME_SQL = """
SELECT d.department_name
FROM public.demo_users u
JOIN public.demo_departments d ON u.department_id = d.department_id
WHERE u.user_id = %s
LIMIT 1
"""


def ensure_read_only_query(query: str) -> None:
    """読み取り専用クエリかどうかを検証する。

    Args:
      query: 実行対象SQL。

    Raises:
      ValueError: SELECT 以外のSQLが渡された場合。

    要件トレーサビリティ:
      要件ID: RQ-EX-READ-ONLY-EXTERNAL-DEPARTMENT-DB
      設計ID: DS-MD-READ-ONLY-EXTERNAL-DEPARTMENT-DB-EX-READ-ONLY-EXTERNAL-DEPARTMENT-DB
      要件概要: 外部DBは読み取り専用で使用し、更新操作を禁止する。
      設計概要: 実行前にSQL先頭を検証して更新系SQLの実行を拒否する。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
    """

    normalized = " ".join(query.strip().split()).lower()
    if not normalized.startswith("select "):
        raise ValueError("外部DBには読み取り専用クエリのみ許可されています")


def get_department_name_by_login_id(login_id: str) -> str | None:
    """login_id(user_id)に対応する部署名を外部DBから取得する。

    Args:
      login_id: 内部ユーザーのログインID（外部 user_id と同一値）。

    Returns:
      部署名。未設定・未取得時は None。

    要件トレーサビリティ:
      要件ID: RQ-EX-CONNECT-EXTERNAL-DEPARTMENT-DB
      設計ID: DS-IF-CONNECT-EXTERNAL-DEPARTMENT-DB-EX-CONNECT-EXTERNAL-DEPARTMENT-DB
      要件概要: login_id=user_id の一致で部署名を取得して表示に利用する。
      設計概要: 環境変数の接続先を使ってSELECTを実行し、部署名を返す。
      呼び出し先設計ID: DS-MD-READ-ONLY-EXTERNAL-DEPARTMENT-DB-EX-READ-ONLY-EXTERNAL-DEPARTMENT-DB
      呼び出し元設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
    """

    if not login_id:
        return None

    use_mock = os.getenv("EXTERNAL_DEPARTMENT_DB_USE_MOCK", "").strip() == "1"
    connect_func = None
    connect_args = ()

    if use_mock:
        spec = importlib.util.spec_from_file_location("psycopg_mock", MOCK_FILE_PATH)
        if spec is None or spec.loader is None:
            return None
        psycopg_mock = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(psycopg_mock)
        connect_func = psycopg_mock.connect
    else:
        if psycopg is None:
            return None
        dsn = os.getenv("EXTERNAL_DEPARTMENT_DB_URL", "").strip()
        if not dsn:
            return None
        connect_func = psycopg.connect
        connect_args = (dsn,)

    ensure_read_only_query(SELECT_DEPARTMENT_NAME_SQL)
    with connect_func(*connect_args) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_DEPARTMENT_NAME_SQL, (login_id,))
            row = cursor.fetchone()

    if row is None:
        return None
    department_name = row[0]
    if department_name is None:
        return None
    return str(department_name)

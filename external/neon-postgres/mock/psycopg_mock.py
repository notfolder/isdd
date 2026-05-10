"""psycopg向けの外部部署DBモック実装。

このモジュールは、`psycopg.connect` を差し替えて、
外部DB接続なしで部署名取得クエリを検証するための最小モックを提供する。

要件意図:
- SQL文字列を簡易検索して `user_id` を抽出する
- `user_id` が既知ユーザーなら部署名を返す
- 未知ユーザーなら `NULL` 相当（Pythonでは `None`）を返す
"""

from __future__ import annotations

import re
from typing import Any
from unittest.mock import patch


# 既存Neonデータを前提にした最小モックデータ。
DEFAULT_DEPARTMENT_BY_USER_ID: dict[str, str] = {
    "U001": "営業部",
    "U002": "開発部",
    "U003": "人事部",
    "U004": "経理部",
    "U005": "情報システム部",
    "U006": "営業部",
    "U007": "開発部",
    "U008": "人事部",
    "U009": "経理部",
    "U010": "情報システム部",
}


USER_ID_LITERAL_PATTERN = re.compile(r"user_id\s*=\s*'([^']+)'", re.IGNORECASE)


def _extract_user_id(query: str, params: Any) -> str | None:
    """SQLとパラメータから user_id を抽出する。"""

    if isinstance(params, dict):
        value = params.get("user_id")
        if isinstance(value, str) and value:
            return value

    if isinstance(params, (list, tuple)) and params:
        first = params[0]
        if isinstance(first, str) and first:
            return first

    literal_match = USER_ID_LITERAL_PATTERN.search(query)
    if literal_match:
        return literal_match.group(1)

    return None


def _normalize_sql(query: str) -> str:
    """SQLを簡易比較用に正規化する。"""

    return " ".join(query.lower().split())


class MockCursor:
    """psycopgカーソル相当の最小モック。"""

    def __init__(self, department_by_user_id: dict[str, str]) -> None:
        self._department_by_user_id = department_by_user_id
        self._rows: list[tuple[Any, ...]] = []

    def __enter__(self) -> "MockCursor":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        self.close()
        return False

    def execute(self, query: str, params: Any = None) -> "MockCursor":
        """SQLを簡易解析し、結果行を内部保持する。"""

        normalized = _normalize_sql(query)
        user_id = _extract_user_id(query, params)

        if "from public.demo_users" not in normalized:
            self._rows = []
            return self

        department_name = None
        if user_id is not None:
            department_name = self._department_by_user_id.get(user_id)

        select_clause = normalized.split(" from ", 1)[0]
        has_department_name = "department_name" in select_clause
        has_user_id = "user_id" in select_clause

        if has_department_name and has_user_id:
            self._rows = [(user_id, department_name)]
            return self

        if has_department_name:
            # 要求仕様: 未知ユーザーはNULLを返す。
            self._rows = [(department_name,)]
            return self

        if has_user_id:
            if user_id and user_id in self._department_by_user_id:
                self._rows = [(user_id,)]
            else:
                self._rows = []
            return self

        self._rows = []
        return self

    def fetchone(self) -> tuple[Any, ...] | None:
        """1行取得する。"""

        if not self._rows:
            return None
        return self._rows[0]

    def fetchall(self) -> list[tuple[Any, ...]]:
        """全行取得する。"""

        return list(self._rows)

    def close(self) -> None:
        """カーソルを閉じる。"""

        return None


class MockConnection:
    """psycopg接続相当の最小モック。"""

    def __init__(self, department_by_user_id: dict[str, str] | None = None) -> None:
        self._department_by_user_id = dict(
            department_by_user_id or DEFAULT_DEPARTMENT_BY_USER_ID
        )

    def __enter__(self) -> "MockConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        self.close()
        return False

    def cursor(self) -> MockCursor:
        """カーソルを生成する。"""

        return MockCursor(self._department_by_user_id)

    def commit(self) -> None:
        """コミット（モックのため実処理なし）。"""

        return None

    def rollback(self) -> None:
        """ロールバック（モックのため実処理なし）。"""

        return None

    def close(self) -> None:
        """接続を閉じる（モックのため実処理なし）。"""

        return None


def connect(*args: Any, **kwargs: Any) -> MockConnection:
    """`psycopg.connect` 互換のモック関数。"""

    department_by_user_id = kwargs.pop("department_by_user_id", None)
    return MockConnection(department_by_user_id=department_by_user_id)


def patch_psycopg_connect(
    department_by_user_id: dict[str, str] | None = None,
) -> Any:
    """`psycopg.connect` をこのモックに差し替えるpatchを返す。"""

    import psycopg

    def _side_effect(*args: Any, **kwargs: Any) -> MockConnection:
        return connect(*args, **kwargs, department_by_user_id=department_by_user_id)

    return patch.object(psycopg, "connect", side_effect=_side_effect)

"""psycopgモックの最小動作確認。"""

from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent / "psycopg_mock.py"
SPEC = importlib.util.spec_from_file_location("psycopg_mock", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("psycopg_mockの読み込みに失敗しました")

psycopg_mock = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(psycopg_mock)


def _query_department_name(user_id: str):
    query = (
        "SELECT d.department_name "
        "FROM public.demo_users u "
        "JOIN public.demo_departments d ON u.department_id = d.department_id "
        "WHERE u.user_id = %s"
    )
    with psycopg_mock.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            row = cur.fetchone()
    return None if row is None else row[0]


def test_known_user_returns_department_name() -> None:
    result = _query_department_name("U001")
    assert result == "営業部"


def test_unknown_user_returns_none() -> None:
    result = _query_department_name("UX99")
    assert result is None

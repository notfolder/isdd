"""
SQLite接続管理モジュール。

要件ID: RQ-DT-DB-NECESSITY
設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY
要件概要: システム内部DBを必須とし、同時利用時の整合性を維持する。
設計概要: SQLite接続を一元化し、スキーマ初期化とトランザクションの基盤を提供する。
呼び出し先設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY, DS-SC-ASSETS-DT-ASSET-ENTITY, DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "equipment.db"


def get_connection() -> sqlite3.Connection:
    """
    SQLite接続を返す。

    Returns:
        sqlite3.Connection: SQLite接続オブジェクト。

    要件ID: RQ-DT-DB-NECESSITY
    設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY
    要件概要: 内部DBを利用して備品・ユーザー・貸出状態の整合性を維持する。
    設計概要: Rowファクトリを有効化した接続を返し、各リポジトリで共通利用する。
    呼び出し先設計ID: なし
    呼び出し元設計ID: DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY, DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY, DS-CL-LOAN-REPOSITORY-DT-LOAN-STATUS-ENTITY
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

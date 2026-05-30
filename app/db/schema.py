"""
DBスキーマ初期化モジュール。

要件ID: RQ-DT-USER-ACCOUNT-ENTITY
設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY
要件概要: ユーザー、備品、貸出状態を永続化して運用できること。
設計概要: users、assets、loan_statusテーブルを作成し、初期管理ユーザーを投入する。
呼び出し先設計ID: DS-SC-USERS-DT-USER-ACCOUNT-ENTITY, DS-SC-ASSETS-DT-ASSET-ENTITY, DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY
呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
"""

from __future__ import annotations

import hashlib
from sqlite3 import Connection


def _hash_password(raw_password: str) -> str:
    """
    パスワードのSHA-256ハッシュを返す。

    Args:
        raw_password (str): 平文パスワード。

    Returns:
        str: ハッシュ化済み文字列。

    要件ID: RQ-NF-LOW-SECURITY-POLICY
    設計ID: DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
    要件概要: ログイン情報を安全に扱い、平文保存を避ける。
    設計概要: 初期データ投入時に平文を保存せず、ハッシュ化して保持する。
    呼び出し先設計ID: なし
    呼び出し元設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY
    """
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def initialize_schema(conn: Connection) -> None:
    """
    アプリケーションで必要なテーブルを作成し、初期データを投入する。

    Args:
        conn (Connection): SQLite接続。

    要件ID: RQ-DT-DB-NECESSITY
    設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY
    要件概要: 内部DBを利用してデータ整合性を確保する。
    設計概要: 必要テーブルを作成し、管理担当者ログイン用の初期アカウントを投入する。
    呼び出し先設計ID: DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY
    呼び出し元設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            login_id TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_code TEXT NOT NULL UNIQUE,
            asset_name TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('available', 'loaned')),
            version_no INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS loan_status (
            asset_id INTEGER PRIMARY KEY,
            borrower_name TEXT,
            due_date TEXT,
            loaned_at TEXT,
            returned_at TEXT,
            FOREIGN KEY(asset_id) REFERENCES assets(asset_id)
        )
        """
    )

    conn.execute(
        """
        INSERT OR IGNORE INTO users (display_name, login_id, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("総務管理者", "admin", _hash_password("admin123"), "admin", 1),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO users (display_name, login_id, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("一般利用者", "viewer", _hash_password("viewer123"), "viewer", 1),
    )

    conn.execute(
        """
        INSERT OR IGNORE INTO assets (asset_id, asset_code, asset_name, location, status, version_no)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (1, "AST001", "PC-A", "総務棚", "available", 1),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO assets (asset_id, asset_code, asset_name, location, status, version_no)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (2, "AST002", "PC-B", "総務棚", "loaned", 1),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO loan_status (asset_id, borrower_name, due_date, loaned_at, returned_at)
        VALUES (?, ?, ?, datetime('now'), NULL)
        """,
        (2, "山田太郎", "2099-12-31"),
    )
    conn.commit()

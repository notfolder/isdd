"""
DatabaseManager - データベース接続と初期化を管理するクラス

要件トレーサビリティ:
  要件ID: RQ-DT-DB-REQUIRED
  設計ID: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
  要件概要: 備品と利用者のデータを永続化し、アプリ再起動後もデータが残る必要がある
  設計概要: SQLiteデータベースへの接続を管理し、itemsテーブルとusersテーブルを作成する。
           初期管理者ユーザー（admin/admin）を自動作成する。
  呼び出し先: なし（SQLiteライブラリを直接使用）
  呼び出し元: DS-MD-BACKEND-API-FT-LOGIN (main.py)
"""

import sqlite3
import os
from typing import Optional


class DatabaseManager:
    """
    データベース接続と初期化を管理するクラス
    
    要件ID: RQ-DT-DB-REQUIRED
    設計ID: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
    """
    
    def __init__(self, db_path: str = "/app/data/equipment.db"):
        """
        DatabaseManagerを初期化する
        
        Args:
            db_path (str): データベースファイルのパス
        
        要件ID: RQ-DT-DB-REQUIRED
        設計ID: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        self.db_path = db_path
    
    def connect(self) -> sqlite3.Connection:
        """
        データベースに接続する
        
        Returns:
            sqlite3.Connection: データベース接続オブジェクト
        
        要件ID: RQ-DT-DB-REQUIRED
        設計ID: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        要件概要: データベースが必要
        設計概要: SQLiteデータベースファイルに接続し、コネクションを返す
        """
        # データベースディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize(self) -> None:
        """
        データベースを初期化する（テーブル作成と初期データ投入）
        
        要件ID: RQ-DT-ITEM, RQ-DT-USER, RQ-DT-DB-REQUIRED
        設計ID: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        要件概要: 備品テーブルと利用者テーブルを作成し、初期管理者を登録する
        設計概要: itemsテーブル（資産管理番号、名称、借り主）とusersテーブル（ユーザーID、氏名、パスワード、権限）を作成し、
                 初期管理者（admin/admin）を登録する
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # itemsテーブル作成
        # 要件ID: RQ-DT-ITEM
        # 設計ID: DS-SC-ITEMS-DT-ITEM
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                asset_number TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                borrower TEXT
            )
        """)
        
        # usersテーブル作成
        # 要件ID: RQ-DT-USER
        # 設計ID: DS-SC-USERS-DT-USER
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        
        conn.commit()
        
        # 初期管理者を作成
        self.create_initial_admin(conn)
        
        conn.close()
    
    def create_initial_admin(self, conn: Optional[sqlite3.Connection] = None) -> None:
        """
        初期管理者ユーザー（admin/admin）を作成する
        
        Args:
            conn (Optional[sqlite3.Connection]): データベース接続（Noneの場合は新規接続）
        
        要件ID: RQ-FT-LOGIN, RQ-NF-ACCESS-CONTROL
        設計ID: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        要件概要: 管理者権限を持つ初期ユーザーを作成する
        設計概要: usersテーブルが空の場合、管理者ユーザー（user_id: admin, password: admin）を自動作成する
        """
        # 循環インポートを避けるため、ここでインポート
        from src.services.auth_service import auth_service
        
        should_close = False
        if conn is None:
            conn = self.connect()
            should_close = True
        
        cursor = conn.cursor()
        
        # ユーザーが存在するか確認
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        # ユーザーが存在しない場合のみ初期管理者を作成
        if count == 0:
            password_hash = auth_service.hash_password("admin")
            cursor.execute(
                "INSERT INTO users (user_id, name, password_hash, role) VALUES (?, ?, ?, ?)",
                ("admin", "管理者", password_hash, "管理者")
            )
            conn.commit()
        
        if should_close:
            conn.close()


# シングルトンインスタンス
db_manager = DatabaseManager()

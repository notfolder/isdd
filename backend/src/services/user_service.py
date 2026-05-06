"""
UserService - 利用者のCRUD操作を管理するクラス

要件トレーサビリティ:
  要件ID: RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST
  設計ID: DS-CL-USER-SERVICE-FT-REGISTER-USER
  要件概要: 利用者の登録、編集、削除、一覧表示を行う
  設計概要: データベースに対して利用者のCRUD操作を実行する
  呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED, DS-CL-AUTH-SERVICE-FT-LOGIN
  呼び出し元: DS-CL-USER-ROUTER-FT-REGISTER-USER
"""

from typing import List, Optional, Dict
import sqlite3
from src.services.auth_service import auth_service


class UserService:
    """
    利用者のCRUD操作を管理するクラス
    
    要件ID: RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST
    設計ID: DS-CL-USER-SERVICE-FT-REGISTER-USER
    """
    
    def get_all_users(self, db_conn: sqlite3.Connection) -> List[Dict]:
        """
        全利用者を取得する
        
        Args:
            db_conn: データベース接続
        
        Returns:
            List[Dict]: 利用者リスト
        
        要件ID: RQ-FT-VIEW-USER-LIST
        設計ID: DS-CL-USER-SERVICE-FT-REGISTER-USER
        要件概要: 利用者一覧を表示する
        設計概要: データベースから全利用者を取得する（パスワードは除く）
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        cursor = db_conn.cursor()
        cursor.execute("SELECT user_id, name, role FROM users")
        rows = cursor.fetchall()
        
        users = []
        for row in rows:
            users.append({
                "user_id": row["user_id"],
                "name": row["name"],
                "role": row["role"]
            })
        
        return users
    
    def get_user(self, db_conn: sqlite3.Connection, user_id: str) -> Optional[Dict]:
        """
        利用者を1件取得する
        
        Args:
            db_conn: データベース接続
            user_id (str): ユーザーID
        
        Returns:
            Optional[Dict]: 利用者情報（存在しない場合はNone）
        
        要件ID: RQ-FT-VIEW-USER-LIST
        設計ID: DS-CL-USER-SERVICE-FT-REGISTER-USER
        要件概要: 指定された利用者の情報を取得する
        設計概要: データベースからユーザーIDで利用者を検索する（パスワードは除く）
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT user_id, name, role FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "role": row["role"]
        }
    
    def create_user(
        self,
        db_conn: sqlite3.Connection,
        user_id: str,
        name: str,
        password: str,
        role: str
    ) -> Dict:
        """
        利用者を登録する
        
        Args:
            db_conn: データベース接続
            user_id (str): ユーザーID
            name (str): 氏名
            password (str): パスワード
            role (str): 権限
        
        Returns:
            Dict: 登録された利用者情報
        
        Raises:
            ValueError: ユーザーIDが重複している場合
        
        要件ID: RQ-FT-REGISTER-USER, RQ-NF-PASSWORD-HASH
        設計ID: DS-CL-USER-SERVICE-FT-REGISTER-USER
        要件概要: 利用者を新規登録する
        設計概要: ユーザーIDの重複をチェックし、パスワードをハッシュ化してデータベースに登録する
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED, DS-CL-AUTH-SERVICE-FT-LOGIN
        """
        # 重複チェック
        existing_user = self.get_user(db_conn, user_id)
        if existing_user is not None:
            raise ValueError(f"ユーザーID {user_id} は既に登録されています")
        
        # パスワードをハッシュ化
        password_hash = auth_service.hash_password(password)
        
        cursor = db_conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, name, password_hash, role) VALUES (?, ?, ?, ?)",
            (user_id, name, password_hash, role)
        )
        db_conn.commit()
        
        return {
            "user_id": user_id,
            "name": name,
            "role": role
        }
    
    def update_user(
        self,
        db_conn: sqlite3.Connection,
        user_id: str,
        name: str,
        password: Optional[str],
        role: str
    ) -> Dict:
        """
        利用者を更新する
        
        Args:
            db_conn: データベース接続
            user_id (str): ユーザーID
            name (str): 氏名
            password (Optional[str]): パスワード（Noneの場合は変更しない）
            role (str): 権限
        
        Returns:
            Dict: 更新された利用者情報
        
        Raises:
            ValueError: 利用者が存在しない場合
        
        要件ID: RQ-FT-EDIT-USER, RQ-NF-PASSWORD-HASH
        設計ID: DS-CL-USER-SERVICE-FT-REGISTER-USER
        要件概要: 利用者情報を編集する
        設計概要: ユーザーIDで利用者を検索し、氏名と権限を更新する。パスワードが指定された場合はハッシュ化して更新する
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED, DS-CL-AUTH-SERVICE-FT-LOGIN
        """
        # 存在チェック
        existing_user = self.get_user(db_conn, user_id)
        if existing_user is None:
            raise ValueError(f"ユーザーID {user_id} の利用者が見つかりません")
        
        cursor = db_conn.cursor()
        
        if password is not None:
            # パスワードが指定された場合はハッシュ化して更新
            password_hash = auth_service.hash_password(password)
            cursor.execute(
                "UPDATE users SET name = ?, password_hash = ?, role = ? WHERE user_id = ?",
                (name, password_hash, role, user_id)
            )
        else:
            # パスワードが指定されていない場合は氏名と権限のみ更新
            cursor.execute(
                "UPDATE users SET name = ?, role = ? WHERE user_id = ?",
                (name, role, user_id)
            )
        
        db_conn.commit()
        
        return self.get_user(db_conn, user_id)
    
    def delete_user(self, db_conn: sqlite3.Connection, user_id: str) -> None:
        """
        利用者を削除する
        
        Args:
            db_conn: データベース接続
            user_id (str): ユーザーID
        
        Raises:
            ValueError: 利用者が存在しない場合
        
        要件ID: RQ-FT-DELETE-USER
        設計ID: DS-CL-USER-SERVICE-FT-REGISTER-USER
        要件概要: 利用者を削除する
        設計概要: ユーザーIDで利用者を検索し、データベースから削除する
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        # 存在チェック
        existing_user = self.get_user(db_conn, user_id)
        if existing_user is None:
            raise ValueError(f"ユーザーID {user_id} の利用者が見つかりません")
        
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        db_conn.commit()


# シングルトンインスタンス
user_service = UserService()

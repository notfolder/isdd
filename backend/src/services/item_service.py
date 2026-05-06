"""
ItemService - 備品のCRUD操作と貸出・返却処理を管理するクラス

要件トレーサビリティ:
  要件ID: RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM, RQ-FT-VIEW-ITEM-LIST
  設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
  要件概要: 備品の登録、編集、削除、貸出、返却、一覧表示を行う
  設計概要: データベースに対して備品のCRUD操作と貸出・返却処理を実行する
  呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
  呼び出し元: DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM
"""

from typing import List, Optional, Dict
import sqlite3


class ItemService:
    """
    備品のCRUD操作と貸出・返却処理を管理するクラス
    
    要件ID: RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM, RQ-FT-VIEW-ITEM-LIST
    設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
    """
    
    def get_all_items(self, db_conn: sqlite3.Connection) -> List[Dict]:
        """
        全備品を取得する
        
        Args:
            db_conn: データベース接続
        
        Returns:
            List[Dict]: 備品リスト
        
        要件ID: RQ-FT-VIEW-ITEM-LIST
        設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
        要件概要: 備品一覧と貸出状況を表示する
        設計概要: データベースから全備品を取得し、貸出状況を含めて返す
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        cursor = db_conn.cursor()
        cursor.execute("SELECT asset_number, name, borrower FROM items")
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "asset_number": row["asset_number"],
                "name": row["name"],
                "borrower": row["borrower"],
                "status": "貸出中" if row["borrower"] else "利用可能"
            })
        
        return items
    
    def get_item(self, db_conn: sqlite3.Connection, asset_number: str) -> Optional[Dict]:
        """
        備品を1件取得する
        
        Args:
            db_conn: データベース接続
            asset_number (str): 資産管理番号
        
        Returns:
            Optional[Dict]: 備品情報（存在しない場合はNone）
        
        要件ID: RQ-FT-VIEW-ITEM-LIST
        設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
        要件概要: 指定された備品の情報を取得する
        設計概要: データベースから資産管理番号で備品を検索し、貸出状況を含めて返す
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT asset_number, name, borrower FROM items WHERE asset_number = ?",
            (asset_number,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return {
            "asset_number": row["asset_number"],
            "name": row["name"],
            "borrower": row["borrower"],
            "status": "貸出中" if row["borrower"] else "利用可能"
        }
    
    def create_item(self, db_conn: sqlite3.Connection, asset_number: str, name: str) -> Dict:
        """
        備品を登録する
        
        Args:
            db_conn: データベース接続
            asset_number (str): 資産管理番号
            name (str): 備品名称
        
        Returns:
            Dict: 登録された備品情報
        
        Raises:
            ValueError: 資産管理番号が重複している場合
        
        要件ID: RQ-FT-REGISTER-ITEM
        設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
        要件概要: 備品を新規登録する
        設計概要: 資産管理番号の重複をチェックし、データベースに備品を登録する
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        # 重複チェック
        existing_item = self.get_item(db_conn, asset_number)
        if existing_item is not None:
            raise ValueError(f"資産管理番号 {asset_number} は既に登録されています")
        
        cursor = db_conn.cursor()
        cursor.execute(
            "INSERT INTO items (asset_number, name, borrower) VALUES (?, ?, ?)",
            (asset_number, name, None)
        )
        db_conn.commit()
        
        return {
            "asset_number": asset_number,
            "name": name,
            "borrower": None,
            "status": "利用可能"
        }
    
    def update_item(self, db_conn: sqlite3.Connection, asset_number: str, name: str) -> Dict:
        """
        備品を更新する
        
        Args:
            db_conn: データベース接続
            asset_number (str): 資産管理番号
            name (str): 備品名称
        
        Returns:
            Dict: 更新された備品情報
        
        Raises:
            ValueError: 備品が存在しない場合
        
        要件ID: RQ-FT-EDIT-ITEM
        設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
        要件概要: 備品情報を編集する
        設計概要: 資産管理番号で備品を検索し、名称を更新する
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        # 存在チェック
        existing_item = self.get_item(db_conn, asset_number)
        if existing_item is None:
            raise ValueError(f"資産管理番号 {asset_number} の備品が見つかりません")
        
        cursor = db_conn.cursor()
        cursor.execute(
            "UPDATE items SET name = ? WHERE asset_number = ?",
            (name, asset_number)
        )
        db_conn.commit()
        
        return self.get_item(db_conn, asset_number)
    
    def delete_item(self, db_conn: sqlite3.Connection, asset_number: str) -> None:
        """
        備品を削除する
        
        Args:
            db_conn: データベース接続
            asset_number (str): 資産管理番号
        
        Raises:
            ValueError: 備品が存在しない場合
        
        要件ID: RQ-FT-DELETE-ITEM
        設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
        要件概要: 備品を削除する
        設計概要: 資産管理番号で備品を検索し、データベースから削除する
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        # 存在チェック
        existing_item = self.get_item(db_conn, asset_number)
        if existing_item is None:
            raise ValueError(f"資産管理番号 {asset_number} の備品が見つかりません")
        
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM items WHERE asset_number = ?", (asset_number,))
        db_conn.commit()
    
    def lend_item(self, db_conn: sqlite3.Connection, asset_number: str, borrower: str) -> Dict:
        """
        備品を貸出する
        
        Args:
            db_conn: データベース接続
            asset_number (str): 資産管理番号
            borrower (str): 借り主（利用者の氏名）
        
        Returns:
            Dict: 更新された備品情報
        
        Raises:
            ValueError: 備品が存在しない、または既に貸出中の場合
        
        要件ID: RQ-FT-LEND-ITEM
        設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
        要件概要: 備品を貸し出す
        設計概要: 備品が利用可能かチェックし、借り主を設定して貸出中にする
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        # 存在チェック
        existing_item = self.get_item(db_conn, asset_number)
        if existing_item is None:
            raise ValueError(f"資産管理番号 {asset_number} の備品が見つかりません")
        
        # 貸出中チェック
        if existing_item["borrower"] is not None:
            raise ValueError(f"備品 {asset_number} は既に貸出中です")
        
        cursor = db_conn.cursor()
        cursor.execute(
            "UPDATE items SET borrower = ? WHERE asset_number = ?",
            (borrower, asset_number)
        )
        db_conn.commit()
        
        return self.get_item(db_conn, asset_number)
    
    def return_item(self, db_conn: sqlite3.Connection, asset_number: str) -> Dict:
        """
        備品を返却する
        
        Args:
            db_conn: データベース接続
            asset_number (str): 資産管理番号
        
        Returns:
            Dict: 更新された備品情報
        
        Raises:
            ValueError: 備品が存在しない、または貸出中でない場合
        
        要件ID: RQ-FT-RETURN-ITEM
        設計ID: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
        要件概要: 備品を返却する
        設計概要: 備品が貸出中かチェックし、借り主をNULLにして利用可能にする
        呼び出し先: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
        """
        # 存在チェック
        existing_item = self.get_item(db_conn, asset_number)
        if existing_item is None:
            raise ValueError(f"資産管理番号 {asset_number} の備品が見つかりません")
        
        # 貸出中チェック
        if existing_item["borrower"] is None:
            raise ValueError(f"備品 {asset_number} は貸出中ではありません")
        
        cursor = db_conn.cursor()
        cursor.execute(
            "UPDATE items SET borrower = NULL WHERE asset_number = ?",
            (asset_number,)
        )
        db_conn.commit()
        
        return self.get_item(db_conn, asset_number)


# シングルトンインスタンス
item_service = ItemService()

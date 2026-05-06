"""
備品管理・貸出管理アプリケーション - メインエントリーポイント

要件トレーサビリティ:
  要件ID: RQ-NF-002
  設計ID: DS-ARC-002
"""

from app import create_app
import os

if __name__ == '__main__':
    """
    アプリケーションを起動
    
    要件トレーサビリティ:
      要件ID: RQ-NF-002
      設計ID: DS-ARC-002
      要件概要: Webアプリケーションを起動。
      設計概要: Flask開発サーバーで実行（本番環境ではgunicorn等を使用）。
      呼び出し先設計ID: 
      呼び出し元設計ID: 
    """
    app = create_app('development')
    app.run(host='127.0.0.1', port=5000, debug=True)

"""
備品管理・貸出管理アプリケーション - Flaskアプリケーションファクトリ

要件トレーサビリティ:
  要件ID: RQ-NF-002
  設計ID: DS-ARC-001, DS-ARC-002
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.models import db
import os

def create_app(config_name='development'):
    """
    Flaskアプリケーションを作成し初期化する
    
    要件トレーサビリティ:
      要件ID: RQ-NF-002
      設計ID: DS-ARC-001, DS-ARC-002
      要件概要: Webアプリケーションを3層構造で構築。オンプレミス環境対応。
      設計概要: Flaskフレームワークを使用。SQLAlchemy ORM で DB 連携。
      呼び出し先設計ID: 
      呼び出し元設計ID: run.py
    """
    app = Flask(__name__)
    
    # 設定
    if config_name == 'development':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///equipment_loan.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
        app.config['JSON_AS_ASCII'] = False
    
    # データベース初期化
    db.init_app(app)
    
    # ルート登録
    from app.routes.auth import auth_bp
    from app.routes.equipments import equipments_bp
    from app.routes.loans import loans_bp
    from app.routes.users import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(equipments_bp, url_prefix='/api/equipments')
    app.register_blueprint(loans_bp, url_prefix='/api/loans')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # テンプレートルート
    from app.routes.web import web_bp
    app.register_blueprint(web_bp)
    
    # コンテキスト内でテーブル作成
    with app.app_context():
        db.create_all()
        _init_default_admin()
    
    return app


def _init_default_admin():
    """
    初期管理者ユーザーを自動作成（存在しない場合）
    
    要件トレーサビリティ:
      要件ID: RQ-AU-001, RQ-FT-005
      設計ID: DS-DB-006, DS-API-001
      要件概要: アプリケーション初回起動時にデフォルト管理者を自動作成。
      設計概要: admin ユーザー（ユーザー名: admin, パスワード: password）を作成。
      呼び出し先設計ID: 
      呼び出し元設計ID: create_app
    """
    from app.models import User
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin_user = User(
            employee_id='ADMIN001',
            name='Administrator',
            username='admin',
            role='admin'
        )
        admin_user.set_password('password')
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created (username: admin, password: password)")

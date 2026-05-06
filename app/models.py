"""
備品管理・貸出管理アプリケーション - データベースモデル定義

要件トレーサビリティ:
  要件ID: RQ-DT-001, RQ-DT-002, RQ-DT-003, RQ-DT-004
  設計ID: DS-DB-001, DS-DB-002, DS-DB-003, DS-DB-004
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    """
    ユーザーマスタ - 社員情報と認証情報を管理
    
    要件トレーサビリティ:
      要件ID: RQ-DT-003, RQ-FT-005
      設計ID: DS-DB-001
      要件概要: 社員の氏名、社員ID、ユーザー名、パスワード、権限（管理者/一般社員）を管理。
      設計概要: SQLAlchemy モデルで users テーブルを定義。パスワードはbcryptでハッシュ化して保存。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-API-001, DS-API-008, DS-API-009, DS-API-010, DS-API-011
    """
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'user'), nullable=False, default='user')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    loans = db.relationship('Loan', backref='borrower', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """
        パスワードをbcryptでハッシュ化して保存
        
        要件トレーサビリティ:
          要件ID: RQ-AU-001, RQ-FT-005
          設計ID: DS-SEC-001
          要件概要: パスワードをハッシュ化して安全に保存。
          設計概要: bcryptを使用してパスワードをハッシュ化。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-001, DS-API-009, DS-API-010
        """
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        入力されたパスワードがハッシュと一致するか検証
        
        要件トレーサビリティ:
          要件ID: RQ-AU-001, RQ-AU-002
          設計ID: DS-SEC-001
          要件概要: ログイン時またはパスワード変更時にパスワードを検証。
          設計概要: bcryptでハッシュ値と比較。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-001, DS-API-003
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self) -> dict:
        """
        ユーザー情報を辞書形式で返す（パスワードハッシュは除外）
        
        要件トレーサビリティ:
          要件ID: RQ-FT-005
          設計ID: DS-API-008, DS-API-009, DS-API-010
          要件概要: ユーザー情報を安全に返す。
          設計概要: パスワードハッシュを除外してJSON化。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-008, DS-API-009, DS-API-010
        """
        return {
            'user_id': self.user_id,
            'employee_id': self.employee_id,
            'name': self.name,
            'username': self.username,
            'role': self.role
        }


class Equipment(db.Model):
    """
    備品マスタ - 管理対象の備品情報を管理
    
    要件トレーサビリティ:
      要件ID: RQ-DT-001, RQ-FT-001, RQ-FT-004
      設計ID: DS-DB-002
      要件概要: 備品の資産管理番号、名前を管理。状態（利用可能/借出中）は貸出記録から動的に判定。
      設計概要: SQLAlchemy モデルで equipments テーブルを定義。資産管理番号はユニーク制約。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-API-004, DS-API-005, DS-API-006, DS-API-007
    """
    __tablename__ = 'equipments'
    
    equipment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_number = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    loans = db.relationship('Loan', backref='equipment', lazy=True, cascade='all, delete-orphan')

    @property
    def status(self) -> str:
        """
        現在の貸出状態を取得（利用可能 or 借出中）
        
        要件トレーサビリティ:
          要件ID: RQ-DT-001, RQ-FT-004
          設計ID: DS-DB-002, DS-API-004
          要件概要: 備品の状態は loans テーブルのレコード有無から判定。未返却のレコードがあれば「借出中」。
          設計概要: 該当備品の未返却レコード（返却日時がNULL）をチェック。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-004
        """
        # 未返却の貸出記録があれば「借出中」
        active_loan = Loan.query.filter_by(equipment_id=self.equipment_id).first()
        return 'borrowed' if active_loan else 'available'

    @property
    def borrowed_by(self) -> str | None:
        """
        現在の借用者名を取得（借出中の場合）
        
        要件トレーサビリティ:
          要件ID: RQ-FT-004, RQ-DT-002
          設計ID: DS-API-004
          要件概要: 備品一覧表示時に借用者名を表示。
          設計概要: 未返却の貸出記録から借用者情報を取得。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-004
        """
        active_loan = Loan.query.filter_by(equipment_id=self.equipment_id).first()
        if active_loan:
            return active_loan.borrower.name
        return None

    def to_dict(self) -> dict:
        """
        備品情報を辞書形式で返す（状態含む）
        
        要件トレーサビリティ:
          要件ID: RQ-FT-004
          設計ID: DS-API-004
          要件概要: 備品情報と状態をJSON化。
          設計概要: asset_number, name, status, borrowed_by を含める。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-004
        """
        return {
            'equipment_id': self.equipment_id,
            'asset_number': self.asset_number,
            'name': self.name,
            'status': self.status,
            'borrowed_by': self.borrowed_by
        }


class Loan(db.Model):
    """
    貸出記録 - 備品の貸出・返却を記録（現在の貸出状況のみ保持）
    
    要件トレーサビリティ:
      要件ID: RQ-DT-002, RQ-DT-004, RQ-FT-002, RQ-FT-003
      設計ID: DS-DB-003
      要件概要: 誰がいつ何を借りたかを記録。返却時にレコードを削除（履歴は保持しない）。
      設計概要: SQLAlchemy モデルで loans テーブルを定義。返却時にレコード削除で対応。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-API-004, DS-API-006, DS-API-007, DS-FLOW-002, DS-FLOW-003
    """
    __tablename__ = 'loans'
    
    loan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipments.equipment_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    loaned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """
        貸出記録を辞書形式で返す
        
        要件トレーサビリティ:
          要件ID: RQ-DT-002
          設計ID: DS-API-006, DS-API-007
          要件概要: 貸出記録の詳細情報を返す。
          設計概要: 借用者名、備品名、貸出日時を含める。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-006, DS-API-007
        """
        return {
            'loan_id': self.loan_id,
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment.name,
            'user_id': self.user_id,
            'borrower_name': self.borrower.name,
            'loaned_at': self.loaned_at.isoformat()
        }


class Session(db.Model):
    """
    セッション管理 - ユーザーセッションを管理（タイムアウト検出用）
    
    要件トレーサビリティ:
      要件ID: RQ-AU-003, RQ-AU-001
      設計ID: DS-DB-004
      要件概要: セッションの作成・更新・削除を管理。30分以上アクセスがないと自動削除。
      設計概要: SQLAlchemy モデルで sessions テーブルを定義。last_activity で最終操作時刻を追跡。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-API-001, DS-API-002, DS-API-012, DS-FLOW-001, DS-FLOW-004
    """
    __tablename__ = 'sessions'
    
    session_id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=False)

    def to_dict(self) -> dict:
        """
        セッション情報を辞書形式で返す
        
        要件トレーサビリティ:
          要件ID: RQ-AU-003
          設計ID: DS-API-012
          要件概要: セッション情報を返す。
          設計概要: session_id, user_id, last_activity を含める。
          呼び出し先設計ID: 
          呼び出し元設計ID: DS-API-012
        """
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }

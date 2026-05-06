"""
認証・セッション管理ユーティリティ

要件トレーサビリティ:
  要件ID: RQ-AU-001, RQ-AU-003
  設計ID: DS-SEC-001, DS-API-012
"""

from app.models import Session, User, db
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import secrets

# セッションタイムアウト時間（分）
SESSION_TIMEOUT_MINUTES = 30


def create_session(user_id: int) -> str:
    """
    ユーザーのセッションを作成
    
    要件トレーサビリティ:
      要件ID: RQ-AU-001, RQ-AU-003
      設計ID: DS-FLOW-001, DS-DB-004
      要件概要: ユーザーログイン時に新規セッションを作成。セッションIDは安全な乱数で生成。
      設計概要: secrets.token_urlsafe()でセッションIDを生成。sessions テーブルに保存。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-API-001
    """
    session_id = secrets.token_urlsafe(32)
    ip_address = request.remote_addr or '0.0.0.0'
    
    session = Session(
        session_id=session_id,
        user_id=user_id,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        ip_address=ip_address
    )
    db.session.add(session)
    db.session.commit()
    
    return session_id


def validate_session(session_id: str) -> tuple[User | None, bool]:
    """
    セッションを検証し、タイムアウト判定を実施
    
    要件トレーサビリティ:
      要件ID: RQ-AU-003
      設計ID: DS-API-012, DS-FLOW-004
      要件概要: 全API呼び出し前にセッション検証。30分以上アクセスがないと自動ログアウト。
      設計概要: last_activity から現在時刻までの経過時間を計算。30分以上の場合はセッション削除し None を返す。
      呼び出し先設計ID: 
      呼び出し元設計ID: session_required デコレータ
    """
    session = Session.query.filter_by(session_id=session_id).first()
    
    if not session:
        return None, False
    
    # タイムアウト判定
    elapsed = datetime.utcnow() - session.last_activity
    if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        # セッション削除
        db.session.delete(session)
        db.session.commit()
        return None, True  # タイムアウトで削除
    
    # last_activity を更新
    session.last_activity = datetime.utcnow()
    db.session.commit()
    
    user = User.query.get(session.user_id)
    return user, False


def delete_session(session_id: str) -> bool:
    """
    セッションを削除（ログアウト時）
    
    要件トレーサビリティ:
      要件ID: RQ-AU-003
      設計ID: DS-API-002, DS-FLOW-001
      要件概要: ログアウト時にセッションレコードを削除。
      設計概要: 対応するセッションレコードを sessions テーブルから削除。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-API-002
    """
    session = Session.query.filter_by(session_id=session_id).first()
    if session:
        db.session.delete(session)
        db.session.commit()
        return True
    return False


def session_required(f):
    """
    セッション検証デコレータ - API エンドポイント保護
    
    要件トレーサビリティ:
      要件ID: RQ-AU-003
      設計ID: DS-SEC-001, DS-API-001
      要件概要: 認証が必要なエンドポイントを保護。セッション検証後に処理を続行。
      設計概要: Cookie からセッションIDを取得。validate_session() でユーザー情報を取得。失敗時は401エラー。
      呼び出し先設計ID: 
      呼び出し元設計ID: 各API エンドポイント
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        user, is_timeout = validate_session(session_id)
        if not user:
            response = jsonify({'success': False, 'error': 'Session expired' if is_timeout else 'Invalid session'})
            response.status_code = 401
            if is_timeout:
                response.delete_cookie('session_id')
            return response
        
        # ユーザー情報をリクエストコンテキストに追加
        request.user = user
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    管理者権限が必要なエンドポイント用デコレータ
    
    要件トレーサビリティ:
      要件ID: RQ-AC-001, RQ-NF-003
      設計ID: DS-SEC-002, DS-API-001
      要件概要: 管理者のみがアクセス可能な操作を保護。
      設計概要: session_required の後に role='admin' をチェック。
      呼び出し先設計ID: 
      呼び出し元設計ID: 各管理者限定API
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        user, _ = validate_session(session_id)
        if not user:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        if user.role != 'admin':
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        
        request.user = user
        return f(*args, **kwargs)
    
    return decorated_function

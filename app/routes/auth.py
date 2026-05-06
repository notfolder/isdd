"""
認証関連のAPIエンドポイント

要件トレーサビリティ:
  要件ID: RQ-AU-001, RQ-AU-002, RQ-AU-003
  設計ID: DS-API-001, DS-API-002, DS-API-003, DS-FLOW-001
"""

from flask import Blueprint, request, jsonify, make_response
from app.models import User, db
from app.utils.auth_utils import create_session, delete_session, session_required, validate_session

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    ログイン処理 - ユーザー認証とセッション生成
    
    要件トレーサビリティ:
      要件ID: RQ-AU-001, RQ-FT-005
      設計ID: DS-API-001, DS-FLOW-001
      要件概要: ユーザー名とパスワードでログイン。成功時にセッションIDを発行。
      設計概要: リクエストからユーザー名とパスワードを取得。ユーザーを検索し、パスワード検証。成功時にセッション作成し、Cookie に設定。
      呼び出し先設計ID: DB User.query, User.check_password, create_session
      呼び出し元設計ID: DS-UI-001
    """
    data = request.get_json()
    
    # バリデーション
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'success': False, 'error': 'Username and password are required'}), 400
    
    username = data.get('username').strip()
    password = data.get('password')
    
    # ユーザー検索
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    
    # セッション作成
    session_id = create_session(user.user_id)
    
    # レスポンス作成
    response = make_response(jsonify({
        'success': True,
        'session_id': session_id,
        'user_id': user.user_id,
        'role': user.role,
        'name': user.name
    }), 200)
    
    # セッションID をCookie に設定（HttpOnly, Secure）
    response.set_cookie('session_id', session_id, httponly=True, secure=False)  # secure=False for development
    
    return response


@auth_bp.route('/logout', methods=['POST'])
@session_required
def logout():
    """
    ログアウト処理 - セッション削除
    
    要件トレーサビリティ:
      要件ID: RQ-AU-003
      設計ID: DS-API-002, DS-SEC-001
      要件概要: ログアウト時にセッションレコードを削除。
      設計概要: Cookie からセッションIDを取得。delete_session() でセッション削除。Cookie も削除。
      呼び出し先設計ID: delete_session
      呼び出し元設計ID: DS-UI-002
    """
    session_id = request.cookies.get('session_id')
    delete_session(session_id)
    
    response = make_response(jsonify({'success': True, 'message': 'Logged out'}), 200)
    response.delete_cookie('session_id')
    
    return response


@auth_bp.route('/change-password', methods=['POST'])
@session_required
def change_password():
    """
    パスワード変更処理 - 現在のパスワード検証後に新パスワードに変更
    
    要件トレーサビリティ:
      要件ID: RQ-AU-002, RQ-FT-005
      設計ID: DS-API-003, DS-SEC-001
      要件概要: ユーザーが自分のパスワードを変更。現在のパスワード検証後に新パスワードを設定。
      設計概要: リクエストから現在のパスワードと新パスワード（2回）を取得。現在のパスワードが正しいことを確認後、新パスワードをハッシュ化して保存。
      呼び出し先設計ID: User.check_password, User.set_password
      呼び出し元設計ID: DS-UI-006
    """
    user = request.user
    data = request.get_json()
    
    # バリデーション
    if not data:
        return jsonify({'success': False, 'error': 'Request body is required'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    new_password_confirm = data.get('new_password_confirm')
    
    if not all([current_password, new_password, new_password_confirm]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    # 現在のパスワード検証
    if not user.check_password(current_password):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
    
    # 新パスワードが一致するか確認
    if new_password != new_password_confirm:
        return jsonify({'success': False, 'error': 'New passwords do not match'}), 400
    
    # パスワード変更
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed'}), 200

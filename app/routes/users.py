"""
ユーザー管理関連のAPIエンドポイント

要件トレーサビリティ:
  要件ID: RQ-FT-005, RQ-DT-003
  設計ID: DS-API-008, DS-API-009, DS-API-010, DS-API-011
"""

from flask import Blueprint, request, jsonify
from app.models import User, Loan, db
from app.utils.auth_utils import admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
@admin_required
def get_users():
    """
    ユーザー一覧を取得（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-005, RQ-DT-003
      設計ID: DS-API-008, DS-DB-001
      要件概要: 全ユーザーを一覧取得。
      設計概要: 管理者権限チェック後、users テーブル全件を社員ID昇順で取得。パスワードハッシュは除外。
      呼び出し先設計ID: User.to_dict
      呼び出し元設計ID: DS-UI-005
    """
    users = User.query.order_by(User.employee_id).all()
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in users]
    }), 200


@users_bp.route('', methods=['POST'])
@admin_required
def create_user():
    """
    新規ユーザーを登録（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-005, RQ-DT-003
      設計ID: DS-API-009, DS-DB-001
      要件概要: 管理者が新規ユーザーを登録。ユーザー名と社員ID は重複不可。
      設計概要: 管理者権限チェック後、リクエストからユーザー情報を取得。重複チェック実施。パスワードをハッシュ化して users テーブルにINSERT。
      呼び出し先設計ID: User.set_password
      呼び出し元設計ID: DS-UI-005
    """
    data = request.get_json()
    
    # バリデーション
    if not data:
        return jsonify({'success': False, 'error': 'Request body is required'}), 400
    
    employee_id = data.get('employee_id', '').strip()
    name = data.get('name', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'user').strip()
    
    if not all([employee_id, name, username, password]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    if role not in ['admin', 'user']:
        return jsonify({'success': False, 'error': 'Role must be admin or user'}), 400
    
    # employee_id と username の重複チェック
    existing_emp = User.query.filter_by(employee_id=employee_id).first()
    if existing_emp:
        return jsonify({'success': False, 'error': 'Employee ID already exists'}), 400
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'success': False, 'error': 'Username already exists'}), 400
    
    # 新規ユーザーを作成
    new_user = User(
        employee_id=employee_id,
        name=name,
        username=username,
        role=role
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user_id': new_user.user_id,
        'message': 'User registered'
    }), 201


@users_bp.route('/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """
    ユーザー情報を更新（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-005, RQ-DT-003
      設計ID: DS-API-010, DS-DB-001
      要件概要: 既存ユーザーの情報を更新。
      設計概要: 管理者権限チェック後、更新対象ユーザーを検索。username と employee_id の重複チェック（自分以外）。users テーブルをUPDATE。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-005
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body is required'}), 400
    
    employee_id = data.get('employee_id', '').strip()
    name = data.get('name', '').strip()
    username = data.get('username', '').strip()
    role = data.get('role', '').strip()
    
    if not all([employee_id, name, username, role]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    if role not in ['admin', 'user']:
        return jsonify({'success': False, 'error': 'Role must be admin or user'}), 400
    
    # employee_id と username の重複チェック（自分以外）
    if employee_id != user.employee_id:
        existing_emp = User.query.filter_by(employee_id=employee_id).first()
        if existing_emp:
            return jsonify({'success': False, 'error': 'Employee ID already exists'}), 400
    
    if username != user.username:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
    
    # 情報を更新
    user.employee_id = employee_id
    user.name = name
    user.username = username
    user.role = role
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User updated'}), 200


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    ユーザーを削除（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-005, RQ-DT-003
      設計ID: DS-API-011, DS-DB-001
      要件概要: ユーザーを削除。管理者ユーザーの削除は禁止。
      設計概要: 管理者権限チェック後、削除対象ユーザーを検索。admin ユーザーの削除を禁止。該当ユーザーが貸出中の備品を持たないか確認。users テーブルからDELETE。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-005
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # admin ユーザーの削除を禁止
    if user.role == 'admin':
        return jsonify({'success': False, 'error': 'Cannot delete admin users'}), 400
    
    # 該当ユーザーが貸出中の備品を持たないか確認
    active_loans = Loan.query.filter_by(user_id=user_id).first()
    if active_loans:
        return jsonify({'success': False, 'error': 'User has borrowed items'}), 400
    
    # ユーザーを削除
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted'}), 200

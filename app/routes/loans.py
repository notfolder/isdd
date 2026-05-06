"""
貸出・返却関連のAPIエンドポイント

要件トレーサビリティ:
  要件ID: RQ-FT-002, RQ-FT-003, RQ-DT-002
  設計ID: DS-API-006, DS-API-007, DS-FLOW-002, DS-FLOW-003
"""

from flask import Blueprint, request, jsonify
from app.models import Loan, Equipment, User, db
from app.utils.auth_utils import admin_required

loans_bp = Blueprint('loans', __name__)


@loans_bp.route('', methods=['POST'])
@admin_required
def create_loan():
    """
    貸出処理 - 備品の貸出記録を作成（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-002, RQ-DT-002
      設計ID: DS-API-006, DS-DB-003, DS-FLOW-002
      要件概要: ユーザーが備品を借り出す際に貸出記録を作成。1回の処理で1つの備品のみ対象。
      設計概要: equipment_id と user_id を受け取り。equipment_id と user_id の存在確認。該当 equipment_id が既に借出中か確認。ない場合は loans テーブルにINSERT。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-004
    """
    data = request.get_json()
    
    # バリデーション
    if not data:
        return jsonify({'success': False, 'error': 'Request body is required'}), 400
    
    equipment_id = data.get('equipment_id')
    user_id = data.get('user_id')
    
    if not equipment_id or not user_id:
        return jsonify({'success': False, 'error': 'Equipment ID and user ID are required'}), 400
    
    # equipment_id と user_id の存在確認
    equipment = Equipment.query.get(equipment_id)
    user = User.query.get(user_id)
    
    if not equipment:
        return jsonify({'success': False, 'error': 'Equipment not found'}), 404
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # 該当 equipment_id が既に借出中か確認
    existing_loan = Loan.query.filter_by(equipment_id=equipment_id).first()
    if existing_loan:
        return jsonify({'success': False, 'error': 'Equipment is already borrowed'}), 400
    
    # 新規貸出記録を作成
    loan = Loan(
        equipment_id=equipment_id,
        user_id=user_id
    )
    db.session.add(loan)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'loan_id': loan.loan_id,
        'message': 'Equipment loaned'
    }), 201


@loans_bp.route('/<int:equipment_id>', methods=['DELETE'])
@admin_required
def return_equipment(equipment_id):
    """
    返却処理 - 貸出記録を削除し、備品を利用可能に戻す（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-003, RQ-DT-004
      設計ID: DS-API-007, DS-DB-003, DS-FLOW-003
      要件概要: ユーザーが備品を返却する際に貸出記録を削除。確認画面なし、即座に実行。
      設計概要: equipment_id を URL パスから取得。loans テーブルで該当レコードを検索。存在する場合は削除。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-002（返却ボタン）
    """
    # 貸出記録を検索
    loan = Loan.query.filter_by(equipment_id=equipment_id).first()
    
    if not loan:
        return jsonify({'success': False, 'error': 'Equipment is not currently borrowed'}), 404
    
    # 貸出記録を削除
    db.session.delete(loan)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Equipment returned'}), 200

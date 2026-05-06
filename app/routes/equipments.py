"""
備品管理関連のAPIエンドポイント

要件トレーサビリティ:
  要件ID: RQ-FT-001, RQ-FT-004, RQ-DT-001
  設計ID: DS-API-004, DS-API-005
"""

from flask import Blueprint, request, jsonify
from app.models import Equipment, db
from app.utils.auth_utils import session_required, admin_required

equipments_bp = Blueprint('equipments', __name__)


@equipments_bp.route('', methods=['GET'])
@session_required
def get_equipments():
    """
    備品一覧を取得（全ユーザー対象、貸出状態を含む）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-004, RQ-DT-001
      設計ID: DS-API-004, DS-DB-002, DS-DB-003
      要件概要: 全備品を一覧取得し、各備品の貸出状態（利用可能/借出中）と借用者名を返す。
      設計概要: 全権限でアクセス可能。equipments テーブル全件を備品名の昇順で取得。各備品について loans テーブルをチェックして状態判定。
      呼び出し先設計ID: Equipment.to_dict
      呼び出し元設計ID: DS-UI-002
    """
    # 備品を名前の昇順で取得
    equipments = Equipment.query.order_by(Equipment.name).all()
    
    return jsonify({
        'success': True,
        'equipments': [eq.to_dict() for eq in equipments]
    }), 200


@equipments_bp.route('', methods=['POST'])
@admin_required
def register_equipment():
    """
    新規備品を登録（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-001, RQ-DT-001
      設計ID: DS-API-005, DS-DB-002
      要件概要: 管理者が新しい備品をシステムに登録。資産管理番号は重複不可。
      設計概要: 管理者権限チェック後、リクエストから資産管理番号と備品名を取得。重複チェック実施後、equipments テーブルにINSERT。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-003
    """
    data = request.get_json()
    
    # バリデーション
    if not data:
        return jsonify({'success': False, 'error': 'Request body is required'}), 400
    
    asset_number = data.get('asset_number', '').strip()
    name = data.get('name', '').strip()
    
    if not asset_number or not name:
        return jsonify({'success': False, 'error': 'Asset number and name are required'}), 400
    
    # 資産番号の重複チェック
    existing = Equipment.query.filter_by(asset_number=asset_number).first()
    if existing:
        return jsonify({'success': False, 'error': 'Asset number already exists'}), 400
    
    # 新規備品を作成
    equipment = Equipment(
        asset_number=asset_number,
        name=name
    )
    db.session.add(equipment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'equipment_id': equipment.equipment_id,
        'message': 'Equipment registered'
    }), 201

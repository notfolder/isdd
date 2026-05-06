"""
Webアプリケーション UI ルート - テンプレート描写

要件トレーサビリティ:
  要件ID: RQ-FT-001, RQ-FT-002, RQ-FT-003, RQ-FT-004, RQ-FT-005, RQ-NF-003
  設計ID: DS-UI-001, DS-UI-002, DS-UI-003, DS-UI-004, DS-UI-005, DS-UI-006
"""

from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.auth_utils import session_required, admin_required, validate_session

web_bp = Blueprint('web', __name__)


@web_bp.route('/', methods=['GET'])
def index():
    """
    ログインページ - ユーザー認証画面
    
    要件トレーサビリティ:
      要件ID: RQ-AU-001, RQ-FT-005
      設計ID: DS-UI-001, DS-FLOW-001
      要件概要: アプリケーション初期画面。ユーザー名とパスワード入力フォーム。
      設計概要: ログインフォームを表示。POST時に /api/auth/login へ送信。成功時に /equipments へリダイレクト。
      呼び出し先設計ID: 
      呼び出し元設計ID: ブラウザアクセス
    """
    # セッション有効チェック
    session_id = request.cookies.get('session_id')
    if session_id:
        user, _ = validate_session(session_id)
        if user:
            # 既にログイン済み
            return redirect(url_for('web.equipment_list'))
    
    return render_template('login.html')


@web_bp.route('/equipments', methods=['GET'])
@session_required
def equipment_list():
    """
    備品一覧画面 - 全備品と貸出状態を表示
    
    要件トレーサビリティ:
      要件ID: RQ-FT-004
      設計ID: DS-UI-002, DS-DB-002, DS-DB-003, DS-FLOW-002
      要件概要: 全備品を一覧表示。各備品の貸出状態（利用可能/借出中）と借用者名を表示。
      設計概要: /api/equipments へ GET リクエスト送信。返却ボタンは管理者のみ表示。借出処理は /loan-process へ遷移。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-001（ログイン後）
    """
    user = request.user
    
    return render_template('equipment_list.html', user=user)


@web_bp.route('/equipment/register', methods=['GET', 'POST'])
@admin_required
def register_equipment():
    """
    備品登録画面 - 新規備品登録フォーム（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-001, RQ-NF-003
      設計ID: DS-UI-003, DS-FLOW-002
      要件概要: 管理者が新しい備品を登録。資産管理番号と備品名を入力。
      設計概要: GET 時に登録フォーム表示。POST 時に /api/equipments へ送信。成功時に /equipments へリダイレクト。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-002（登録ボタン）
    """
    user = request.user
    
    return render_template('equipment_register.html', user=user)


@web_bp.route('/loan-process/<int:equipment_id>', methods=['GET', 'POST'])
@admin_required
def loan_process(equipment_id):
    """
    貸出処理画面 - ユーザー選択と貸出実行（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-002
      設計ID: DS-UI-004, DS-FLOW-002
      要件概要: 管理者が指定備品をユーザーに貸し出す。ユーザーを選択して実行。
      設計概要: GET 時に /api/users へ GET リクエストでユーザー一覧取得。ユーザー選択フォーム表示。POST 時に /api/loans へ POST送信。成功時に /equipments へリダイレクト。
      呼び出し先設計ID: 
      呼び出し元設計ID: DS-UI-002（借出ボタン）
    """
    user = request.user
    
    return render_template('loan_process.html', user=user, equipment_id=equipment_id)


@web_bp.route('/user-management', methods=['GET', 'POST'])
@admin_required
def user_management():
    """
    ユーザー管理画面 - ユーザー情報の CRUD（管理者のみ）
    
    要件トレーサビリティ:
      要件ID: RQ-FT-005, RQ-NF-003
      設計ID: DS-UI-005, DS-DB-001
      要件概要: 管理者が全ユーザー情報を管理。一覧表示、新規作成、編集、削除操作。
      設計概要: GET 時に /api/users へ GET リクエストでユーザー一覧取得。編集・削除のための UI を提供。POST 時に対応 API へ送信。
      呼び出し先設計ID: 
      呼び出し元設計ID: メニューナビゲーション
    """
    user = request.user
    
    return render_template('user_management.html', user=user)


@web_bp.route('/password-change', methods=['GET', 'POST'])
@session_required
def password_change():
    """
    パスワード変更画面 - ユーザーが自分のパスワードを変更
    
    要件トレーサビリティ:
      要件ID: RQ-AU-002
      設計ID: DS-UI-006, DS-FLOW-004
      要件概要: ユーザーが自分のパスワードを変更。現在のパスワード入力後に新パスワード設定。
      設計概要: GET 時にパスワード変更フォーム表示。POST 時に /api/auth/change-password へ送信。成功時は /equipments へリダイレクト。
      呼び出し先設計ID: 
      呼び出し元設計ID: メニューナビゲーション
    """
    user = request.user
    
    return render_template('password_change.html', user=user)

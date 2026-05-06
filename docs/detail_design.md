# 備品管理・貸出管理アプリ 詳細設計書

## 1. システムアーキテクチャ

### 1.1 全体構成

**DS-ARC-001**: システム構成
- **要件対応**: RQ-NF-002
- **アーキテクチャ**: 3層Webアプリケーション
  - **プレゼンテーション層**: Webブラウザ（HTML/CSS/JavaScript）
  - **アプリケーション層**: Webサーバー（Python Flask / Node.js Express など）
  - **データ層**: リレーショナルDB（SQLite / PostgreSQL など）
  
**DS-ARC-002**: 運用環境
- **要件対応**: RQ-NF-002
- **環境**: オンプレミス
- **サーバー**: 単一サーバー構成
- **データベース**: ローカルDB（オンプレミスに保存）
- **同時接続**: 最大10セッション

---

## 2. データベース設計

### 2.1 テーブル定義

**DS-DB-001**: users テーブル（ユーザーマスタ）
- **要件対応**: RQ-DT-003, RQ-FT-005
- **目的**: 社員情報と認証情報を管理

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| user_id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | ユーザーの一意識別子（内部ID） |
| employee_id | VARCHAR(50) | UNIQUE, NOT NULL | 社員ID |
| name | VARCHAR(255) | NOT NULL | 社員の氏名 |
| username | VARCHAR(100) | UNIQUE, NOT NULL | ログイン用ユーザー名 |
| password | VARCHAR(255) | NOT NULL | ログイン用パスワード（ハッシュ化） |
| role | ENUM('admin', 'user') | NOT NULL | 権限（admin=管理者, user=一般社員） |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新日時 |

**DS-DB-002**: equipments テーブル（備品マスタ）
- **要件対応**: RQ-DT-001, RQ-FT-001, RQ-FT-004
- **目的**: 管理対象の備品情報を管理

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| equipment_id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 備品の内部ID |
| asset_number | VARCHAR(100) | UNIQUE, NOT NULL | 資産管理番号（ユーザー入力） |
| name | VARCHAR(255) | NOT NULL | 備品名 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 登録日時 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新日時 |

**DS-DB-003**: loans テーブル（貸出記録）
- **要件対応**: RQ-DT-002, RQ-FT-002, RQ-FT-003
- **目的**: 貸出・返却を記録（現在の貸出状況のみ保持、返却時に削除）

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| loan_id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 貸出記録の内部ID |
| equipment_id | INTEGER | FOREIGN KEY(equipments), NOT NULL | 備品への参照 |
| user_id | INTEGER | FOREIGN KEY(users), NOT NULL | 借用者への参照 |
| loaned_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 貸出日時 |

**DS-DB-004**: sessions テーブル（セッション管理）
- **要件対応**: RQ-AU-003
- **目的**: ユーザーセッションを管理（タイムアウト検出用）

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| session_id | VARCHAR(255) | PRIMARY KEY | セッションID |
| user_id | INTEGER | FOREIGN KEY(users), NOT NULL | ユーザーへの参照 |
| created_at | DATETIME | NOT NULL | セッション作成日時 |
| last_activity | DATETIME | NOT NULL | 最終操作日時 |
| ip_address | VARCHAR(50) | NOT NULL | クライアントIPアドレス |

### 2.2 インデックス定義

**DS-DB-005**: インデックス設定
- **要件対応**: RQ-NF-001
- **目的**: クエリパフォーマンス向上

| テーブル | カラム | 種類 | 説明 |
|---------|--------|------|------|
| users | username | UNIQUE | ログイン時の検索高速化 |
| users | employee_id | UNIQUE | 社員ID検索の高速化 |
| equipments | asset_number | UNIQUE | 資産番号重複チェック |
| equipments | name | INDEX | 備品一覧の名前順ソート |
| loans | equipment_id | INDEX | 貸出中の備品検索 |
| loans | user_id | INDEX | ユーザーの貸出状況検索 |
| sessions | user_id | INDEX | セッション検索 |
| sessions | last_activity | INDEX | タイムアウト検出 |

### 2.3 初期データ

**DS-DB-006**: 初期管理者ユーザー
- **要件対応**: RQ-AU-001
- **作成タイミング**: アプリケーション初回起動時
- **初期レコード**:
  ```
  employee_id: 'ADMIN001'
  name: 'Administrator'
  username: 'admin'
  password: (password のハッシュ値)
  role: 'admin'
  ```

---

## 3. API設計

### 3.1 認証API

**DS-API-001**: ログイン
- **要件対応**: RQ-AU-001
- **エンドポイント**: POST /api/auth/login
- **リクエスト**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "session_id": "string",
    "user_id": "integer",
    "role": "admin|user",
    "name": "string"
  }
  ```
- **レスポンス（失敗: 401）**:
  ```json
  {
    "success": false,
    "error": "Invalid username or password"
  }
  ```
- **セッション管理**: 
  - セッションIDを生成し sessions テーブルに保存
  - クライアントのCookieにセッションIDを設定（HttpOnly、Secure）
  - last_activity を現在時刻に設定

**DS-API-002**: ログアウト
- **要件対応**: RQ-AU-003
- **エンドポイント**: POST /api/auth/logout
- **リクエスト**: session_id（Cookie から自動取得）
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "message": "Logged out"
  }
  ```
- **処理**: sessions テーブルから該当レコードを削除

**DS-API-003**: パスワード変更
- **要件対応**: RQ-AU-002
- **エンドポイント**: POST /api/auth/change-password
- **認証**: 必須（セッション確認）
- **リクエスト**:
  ```json
  {
    "current_password": "string",
    "new_password": "string"
  }
  ```
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "message": "Password changed"
  }
  ```
- **レスポンス（失敗: 400）**:
  ```json
  {
    "success": false,
    "error": "Current password is incorrect"
  }
  ```
- **検証**: 
  - 現在のパスワードが正しいことを確認（ハッシュ比較）
  - パスワード変更前に確認を実施

### 3.2 備品管理API

**DS-API-004**: 備品一覧取得
- **要件対応**: RQ-FT-004
- **エンドポイント**: GET /api/equipments
- **認証**: 必須（セッション確認）
- **パラメータ**: なし
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "equipments": [
      {
        "equipment_id": "integer",
        "asset_number": "string",
        "name": "string",
        "status": "available|borrowed",
        "borrowed_by": "string (borrower name, null if available)"
      }
    ]
  }
  ```
- **ソート**: 備品名の昇順
- **ステータス判定**:
  - "available": loans テーブルに該当 equipment_id のレコードがない
  - "borrowed": loans テーブルに該当 equipment_id のレコードがある

**DS-API-005**: 備品登録
- **要件対応**: RQ-FT-001
- **エンドポイント**: POST /api/equipments
- **認証**: 必須 + 管理者のみ（role='admin'）
- **リクエスト**:
  ```json
  {
    "asset_number": "string",
    "name": "string"
  }
  ```
- **レスポンス（成功: 201）**:
  ```json
  {
    "success": true,
    "equipment_id": "integer",
    "message": "Equipment registered"
  }
  ```
- **レスポンス（失敗: 400）**:
  ```json
  {
    "success": false,
    "error": "Asset number already exists"
  }
  ```
- **検証**:
  - asset_number の重複チェック（UNIQUE制約）
  - asset_number と name の必須チェック

### 3.3 貸出・返却API

**DS-API-006**: 貸出処理
- **要件対応**: RQ-FT-002
- **エンドポイント**: POST /api/loans
- **認証**: 必須 + 管理者のみ（role='admin'）
- **リクエスト**:
  ```json
  {
    "equipment_id": "integer",
    "user_id": "integer"
  }
  ```
- **レスポンス（成功: 201）**:
  ```json
  {
    "success": true,
    "loan_id": "integer",
    "message": "Equipment loaned"
  }
  ```
- **レスポンス（失敗: 400）**:
  ```json
  {
    "success": false,
    "error": "Equipment is already borrowed"
  }
  ```
- **検証**:
  - equipment_id が存在するか確認
  - user_id が存在するか確認
  - 該当 equipment_id が現在利用可能か確認（loans テーブルにレコードがないか）

**DS-API-007**: 返却処理
- **要件対応**: RQ-FT-003
- **エンドポイント**: DELETE /api/loans/{equipment_id}
- **認証**: 必須 + 管理者のみ（role='admin'）
- **パラメータ**: equipment_id（URL パス）
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "message": "Equipment returned"
  }
  ```
- **レスポンス（失敗: 404）**:
  ```json
  {
    "success": false,
    "error": "Equipment is not currently borrowed"
  }
  ```
- **処理**:
  - 該当 equipment_id の loans レコードを削除（1件のみ）
  - 削除時に確認画面なし（即座に実行）

### 3.4 ユーザー管理API

**DS-API-008**: ユーザー一覧取得
- **要件対応**: RQ-FT-005
- **エンドポイント**: GET /api/users
- **認証**: 必須 + 管理者のみ（role='admin'）
- **パラメータ**: なし
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "users": [
      {
        "user_id": "integer",
        "employee_id": "string",
        "name": "string",
        "username": "string",
        "role": "admin|user"
      }
    ]
  }
  ```
- **ソート**: employee_id の昇順

**DS-API-009**: ユーザー登録
- **要件対応**: RQ-FT-005
- **エンドポイント**: POST /api/users
- **認証**: 必須 + 管理者のみ（role='admin'）
- **リクエスト**:
  ```json
  {
    "employee_id": "string",
    "name": "string",
    "username": "string",
    "password": "string",
    "role": "admin|user"
  }
  ```
- **レスポンス（成功: 201）**:
  ```json
  {
    "success": true,
    "user_id": "integer",
    "message": "User registered"
  }
  ```
- **レスポンス（失敗: 400）**:
  ```json
  {
    "success": false,
    "error": "Username already exists"
  }
  ```
- **検証**:
  - username の重複チェック
  - employee_id の重複チェック
  - 全フィールドの必須チェック

**DS-API-010**: ユーザー更新
- **要件対応**: RQ-FT-005
- **エンドポイント**: PUT /api/users/{user_id}
- **認証**: 必須 + 管理者のみ（role='admin'）
- **リクエスト**:
  ```json
  {
    "employee_id": "string",
    "name": "string",
    "username": "string",
    "role": "admin|user"
  }
  ```
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "message": "User updated"
  }
  ```
- **検証**:
  - 更新対象ユーザーが存在するか確認
  - username の重複チェック（自分以外）
  - employee_id の重複チェック（自分以外）

**DS-API-011**: ユーザー削除
- **要件対応**: RQ-FT-005
- **エンドポイント**: DELETE /api/users/{user_id}
- **認証**: 必須 + 管理者のみ（role='admin'）
- **パラメータ**: user_id（URL パス）
- **レスポンス（成功: 200）**:
  ```json
  {
    "success": true,
    "message": "User deleted"
  }
  ```
- **レスポンス（失敗: 400）**:
  ```json
  {
    "success": false,
    "error": "Cannot delete admin users"
  }
  ```
- **検証**:
  - 削除対象ユーザーが存在するか確認
  - admin ユーザーを削除しようとしていないか確認（admin は削除不可）
  - 該当ユーザーが現在貸出中の備品を持っていないか確認

### 3.5 セッション管理

**DS-API-012**: セッション検証・タイムアウト判定
- **要件対応**: RQ-AU-003
- **実行タイミング**: 全API呼び出し前に実行
- **処理フロー**:
  1. リクエストのCookieからセッションIDを取得
  2. sessions テーブルで該当レコードを検索
  3. last_activity から現在時刻までの経過時間を計算
  4. 30分以上経過している場合は自動ログアウト（セッションレコード削除）、401エラーを返す
  5. 30分以内の場合は last_activity を現在時刻に更新

---

## 4. 画面設計

### 4.1 ログイン画面

**DS-UI-001**: ログイン画面（RQ-UI-001）
- **要件対応**: RQ-AU-001, RQ-FT-004
- **アクセス権限**: 全員（未認証）
- **入力項目**:
  - ユーザー名（テキスト入力）
  - パスワード（パスワード入力）
- **入力検証**:
  - ユーザー名: 必須、1文字以上
  - パスワード: 必須、1文字以上
- **ボタン**:
  - ログインボタン（クリック時に POST /api/auth/login を呼び出し）
- **エラー表示**:
  - ユーザー名またはパスワードが未入力: 「ユーザー名とパスワードを入力してください」
  - 認証失敗: 「ユーザー名またはパスワードが正しくありません」
- **遷移先**:
  - ログイン成功時: 備品一覧画面（RQ-UI-002）へリダイレクト
  - 遷移時にセッション初期化確認

### 4.2 備品一覧画面

**DS-UI-002**: 備品一覧画面（RQ-UI-002）
- **要件対応**: RQ-FT-004, RQ-AC-001, RQ-AC-002
- **アクセス権限**: 全員（認証済み）
- **表示内容**:
  - ヘッダーメニュー（権限に応じて表示内容を変更）
    - 管理者: 備品一覧, 備品登録, 貸出処理, ユーザー管理, パスワード変更, ログアウト
    - 一般社員: 備品一覧, パスワード変更, ログアウト
  - テーブル形式で全備品を表示
    - カラム: 資産管理番号, 備品名, 貸出状態（利用可能/借出中）, 返却ボタン（管理者かつ借出中のみ）
- **テーブルソート**: 備品名の昇順（五十音順）
- **返却ボタン（管理者のみ）**:
  - 表示対象: 貸出状態が「借出中」の行のみ
  - クリック時の処理:
    - 即座に DELETE /api/loans/{equipment_id} を呼び出し
    - 成功時: テーブルをリロード、該当行の状態を「利用可能」に変更
    - 失敗時: エラーメッセージを表示
- **ページ読み込み**:
  - 初期化時に GET /api/equipments を呼び出し、備品一覧を取得
  - 定期的（5秒ごと）にデータを更新

### 4.3 備品登録画面

**DS-UI-003**: 備品登録画面（RQ-UI-003）
- **要件対応**: RQ-FT-001, RQ-AC-001
- **アクセス権限**: 管理者のみ
- **入力項目**:
  - 資産管理番号（テキスト入力）
  - 備品名（テキスト入力）
- **入力検証**:
  - 資産管理番号: 必須、1文字以上、既存との重複チェック
  - 備品名: 必須、1文字以上
- **ボタン**:
  - 登録ボタン（POST /api/equipments を呼び出し）
  - キャンセルボタン（備品一覧画面へ戻る）
- **エラー表示**:
  - 必須項目未入力: 「全ての項目を入力してください」
  - 資産管理番号重複: 「この資産管理番号は既に使用されています」
  - 登録失敗: 「備品の登録に失敗しました」
- **成功時の処理**:
  - 登録完了メッセージを表示
  - 2秒後に備品一覧画面へリダイレクト

### 4.4 貸出処理画面

**DS-UI-004**: 貸出処理画面（RQ-UI-004）
- **要件対応**: RQ-FT-002, RQ-AC-001
- **アクセス権限**: 管理者のみ
- **入力項目**:
  - 借用者（ドロップダウン、users テーブルから全ユーザーを取得）
    - 表示形式: 「社員ID - 名前」
    - ソート: employee_id の昇順
  - 備品（ドロップダウン、loans テーブルに存在しない equipment のみ取得）
    - 表示形式: 「資産管理番号 - 備品名」
    - ソート: 備品名の昇順
- **入力検証**:
  - 借用者: 必須
  - 備品: 必須
- **ボタン**:
  - 貸出ボタン（POST /api/loans を呼び出し）
  - キャンセルボタン（備品一覧画面へ戻る）
- **エラー表示**:
  - 必須項目未選択: 「借用者と備品を選択してください」
  - 備品が借出中: 「選択された備品は既に借り出されています」
  - 貸出失敗: 「貸出処理に失敗しました」
- **成功時の処理**:
  - 貸出完了メッセージを表示
  - 2秒後に備品一覧画面へリダイレクト

### 4.5 ユーザー管理画面

**DS-UI-005**: ユーザー管理画面（RQ-UI-005）
- **要件対応**: RQ-FT-005, RQ-AC-001
- **アクセス権限**: 管理者のみ
- **画面構成**:
  - ユーザー一覧（テーブル）
  - 新規登録フォーム
  
**ユーザー一覧テーブル**:
- カラム: 社員ID, 名前, ユーザー名, 権限, 操作（編集, 削除）
- ソート: employee_id の昇順
- 初期化時に GET /api/users を呼び出し
- 編集ボタン: クリック時にフォームに該当ユーザー情報を填入

**新規登録フォーム**:
- 入力項目:
  - 社員ID（テキスト入力）
  - 名前（テキスト入力）
  - ユーザー名（テキスト入力）
  - パスワード（パスワード入力）
  - 権限（ラジオボタン: 管理者 / 一般社員）
- ボタン:
  - 登録ボタン（新規時: POST /api/users, 編集時: PUT /api/users/{user_id}）
  - クリアボタン（フォームをリセット）

**入力検証**:
- 全フィールド必須
- ユーザー名の重複チェック（自分以外）
- 社員IDの重複チェック（自分以外）

**削除ボタン**:
- クリック時に確認ダイアログを表示: 「このユーザーを削除してもよろしいですか？」
- 確認後に DELETE /api/users/{user_id} を呼び出し
- 制限: admin ユーザーは削除不可（ボタンを表示しない）

### 4.6 パスワード変更画面

**DS-UI-006**: パスワード変更画面（RQ-UI-006）
- **要件対応**: RQ-AU-002, RQ-AC-001, RQ-AC-002
- **アクセス権限**: 全員（認証済み）
- **入力項目**:
  - 現在のパスワード（パスワード入力）
  - 新しいパスワード（パスワード入力）
  - 新しいパスワード（確認用、パスワード入力）
- **入力検証**:
  - 全フィールド必須
  - 新しいパスワード と 新しいパスワード（確認） が一致するか確認
- **ボタン**:
  - 変更ボタン（POST /api/auth/change-password を呼び出し）
  - キャンセルボタン（元の画面に戻る）
- **エラー表示**:
  - 必須項目未入力: 「全ての項目を入力してください」
  - パスワード不一致: 「新しいパスワードが一致しません」
  - 現在のパスワード不正: 「現在のパスワードが正しくありません」
  - 変更失敗: 「パスワード変更に失敗しました」
- **成功時の処理**:
  - 変更完了メッセージを表示
  - 2秒後にログイン画面へリダイレクト（再認証が必要）

---

## 5. 処理フロー設計

### 5.1 ログイン処理フロー

**DS-FLOW-001**: ログイン処理
- **要件対応**: RQ-AU-001, RQ-AU-003
- **フロー**:
  1. ユーザーがログイン画面でユーザー名とパスワードを入力
  2. ログインボタンをクリック
  3. POST /api/auth/login を呼び出し
  4. サーバーで users テーブルからユーザー名で検索
  5. 該当ユーザーが存在しない場合: 401エラーを返す
  6. 存在する場合、パスワードのハッシュ値と比較
  7. 一致しない場合: 401エラーを返す
  8. 一致する場合、セッションIDを生成
  9. sessions テーブルにレコード作成
     - session_id: 生成したID
     - user_id: ログインユーザーのID
     - created_at: 現在時刻
     - last_activity: 現在時刻
     - ip_address: クライアントのIPアドレス
  10. セッションIDをCookieに設定（HttpOnly, Secure）
  11. 応答でセッションIDと権限を返す
  12. クライアント: 権限に応じた画面へ遷移

### 5.2 貸出処理フロー

**DS-FLOW-002**: 貸出処理
- **要件対応**: RQ-FT-002, RQ-DT-002
- **フロー**:
  1. 管理者が貸出処理画面で借用者と備品を選択
  2. 貸出ボタンをクリック
  3. POST /api/loans を呼び出し
  4. サーバーで権限確認（role='admin'）
  5. equipment_id と user_id の存在確認
  6. loans テーブルで該当 equipment_id のレコード存在確認
     - 存在する場合: 400エラー（既に借出中）
     - 存在しない場合: 次へ進む
  7. 新規貸出記録をloans テーブルに追加
     - equipment_id: 選択した備品
     - user_id: 選択したユーザー
     - loaned_at: 現在時刻
  8. 成功応答を返す
  9. クライアント: 備品一覧画面へ遷移、該当備品の状態を「借出中」に更新

### 5.3 返却処理フロー

**DS-FLOW-003**: 返却処理
- **要件対応**: RQ-FT-003, RQ-DT-004
- **フロー**:
  1. 管理者が備品一覧画面の返却ボタンをクリック
  2. DELETE /api/loans/{equipment_id} を呼び出し
  3. サーバーで権限確認（role='admin'）
  4. loans テーブルで該当 equipment_id のレコード検索
     - レコードが存在しない場合: 404エラー
     - レコードが存在する場合: 次へ進む
  5. 該当レコードを loans テーブルから削除
  6. 成功応答を返す
  7. クライアント: 該当備品の状態を「利用可能」に更新

### 5.4 セッションタイムアウト処理フロー

**DS-FLOW-004**: セッションタイムアウト検出
- **要件対応**: RQ-AU-003
- **フロー**:
  1. クライアントがAPIを呼び出し
  2. リクエストのCookieからセッションIDを取得
  3. sessions テーブルで該当レコードを検索
     - レコードが存在しない場合: 401エラー（セッション無効）
     - レコードが存在する場合: 次へ進む
  4. last_activity から現在時刻までの経過時間を計算
  5. 30分以上経過している場合:
     - 該当セッションレコードを削除
     - 401エラーを返す
     - クライアント: ログイン画面へリダイレクト
  6. 30分以内の場合:
     - last_activity を現在時刻に更新
     - APIの処理を続行

---

## 6. セキュリティ設計

### 6.1 認証・認可

**DS-SEC-001**: 認証メカニズム
- **要件対応**: RQ-AU-001, RQ-AU-003, RQ-NF-003
- **認証方式**: セッションベース認証
- **パスワード保存**: bcrypt等でハッシュ化して保存（平文保存禁止）
- **セッションID**: 安全な乱数生成（例：Python secrets.token_urlsafe()）
- **Cookie設定**: HttpOnly（JavaScriptアクセス禁止）, Secure（HTTPS通信のみ）

**DS-SEC-002**: 認可メカニズム
- **要件対応**: RQ-AC-001, RQ-AC-002, RQ-NF-003
- **権限チェック**: 全API呼び出し前に実施
  - セッション存在確認
  - role フィールドの確認
  - 管理者限定操作: role='admin' の確認
- **画面表示制御**: JavaScriptで権限に応じたメニュー表示制御

### 6.2 入力検証

**DS-SEC-003**: 入力検証
- **要件対応**: RQ-NF-003
- **実装箇所**: サーバーサイド（クライアント側でも補助的に実施）
- **検証項目**:
  - 必須フィールドチェック
  - 長さチェック（最大値設定）
  - SQL インジェクション対策：パラメータ化されたクエリ使用
  - XXS対策：出力時にHTMLエスケープ
  - CSRF対策：CSRF トークンの使用

### 6.3 エラーハンドリング

**DS-SEC-004**: エラーハンドリング
- **要件対応**: RQ-NF-003
- **内部エラーの非暴露**: 500エラーは汎用メッセージのみ返す（詳細情報非表示）
- **ログ記録**: エラーをサーバーログに記録（監査不要のため操作ログは不要）
- **エラーレスポンス形式**:
  ```json
  {
    "success": false,
    "error": "ユーザーフレンドリーなメッセージ"
  }
  ```

---

## 7. エラーハンドリング設計

**DS-ERR-001**: HTTP ステータスコード
- **200 OK**: リクエスト成功
- **201 Created**: リソース作成成功
- **400 Bad Request**: クライアント側エラー（入力不正、ビジネスロジック違反）
- **401 Unauthorized**: 認証失敗、セッション無効
- **403 Forbidden**: 認可失敗（権限不足）
- **404 Not Found**: リソース未検出
- **500 Internal Server Error**: サーバーエラー

**DS-ERR-002**: エラーメッセージ定義
- ユーザーに表示するメッセージは日本語で簡潔に記載
- 技術的な詳細情報は非表示（サーバーログのみ）
- 例外的状況でも汎用メッセージ返却

---

## 8. 非機能設計

### 8.1 性能

**DS-PERF-001**: 同時接続対応
- **要件対応**: RQ-NF-001
- **目標**: 同時10セッション対応
- **対応方針**:
  - コネクションプーリング使用
  - キャッシュ層の導入（必要に応じて）
  - インデックス活用（DB設計で定義済み）

**DS-PERF-002**: レスポンス時間
- **要件対応**: RQ-NF-001
- **目標**: 通常操作は1秒以内
- **対応方針**:
  - DBクエリの最適化（インデックス、JOIN管理）
  - N+1クエリ問題の排除

### 8.2 保守性

**DS-MAINT-001**: API設計
- **要件対応**: RQ-NF-002
- **原則**: RESTful設計（GETで取得、POSTで作成、PUTで更新、DELETEで削除）
- **バージョニング**: 初期版は /api/v1/ パス（将来の拡張性確保）

---

## 9. 実装上の注意点

**DS-IMPL-001**: 初期化処理
- アプリケーション初回起動時に:
  1. DBテーブルが存在しない場合は自動作成
  2. users テーブルに admin ユーザーが存在しない場合は作成

**DS-IMPL-002**: トランザクション管理
- 貸出・返却処理は単一トランザクションで実行（途中で失敗しない）

**DS-IMPL-003**: 日時管理
- 全日時は UTC で保存（オンプレミスの時刻設定に依存しない）
- UI表示時にローカルタイムに変換

---

## 10. 要件・設計ID対応表

| 要件ID | 要件名 | 対応設計ID | 説明 |
|--------|--------|-----------|------|
| RQ-DT-001 | 備品属性 | DS-DB-002 | equipments テーブルで実装 |
| RQ-DT-002 | 貸出記録属性 | DS-DB-003 | loans テーブルで実装 |
| RQ-DT-003 | ユーザー属性 | DS-DB-001 | users テーブルで実装 |
| RQ-DT-004 | 返却時レコード削除 | DS-FLOW-003, DS-API-007 | 返却時に loans レコードを削除 |
| RQ-FT-001 | 備品登録 | DS-API-005, DS-UI-003 | 登録画面とAPI で実装 |
| RQ-FT-002 | 貸出処理 | DS-API-006, DS-UI-004, DS-FLOW-002 | 貸出画面と処理ロジックで実装 |
| RQ-FT-003 | 返却処理 | DS-API-007, DS-UI-002, DS-FLOW-003 | 返却ボタンと処理ロジックで実装 |
| RQ-FT-004 | 備品一覧表示 | DS-API-004, DS-UI-002 | 一覧画面とAPIで実装 |
| RQ-FT-005 | ユーザー管理 | DS-API-008～011, DS-UI-005 | 管理画面とAPIで実装 |
| RQ-AU-001 | ログイン | DS-API-001, DS-UI-001, DS-FLOW-001 | ログイン画面と処理で実装 |
| RQ-AU-002 | パスワード変更 | DS-API-003, DS-UI-006 | 変更画面とAPIで実装 |
| RQ-AU-003 | セッション管理 | DS-DB-004, DS-API-012, DS-FLOW-004 | sessions テーブルと自動タイムアウトで実装 |
| RQ-AC-001 | 管理者権限 | DS-SEC-002, DS-API-001～011 | 権限チェックで制御 |
| RQ-AC-002 | 一般社員権限 | DS-SEC-002, DS-UI-002, DS-UI-006 | 画面表示制御で実装 |
| RQ-UI-001 | ログイン画面 | DS-UI-001 | ログイン画面設計 |
| RQ-UI-002 | 備品一覧画面 | DS-UI-002 | 一覧画面設計 |
| RQ-UI-003 | 備品登録画面 | DS-UI-003 | 登録画面設計 |
| RQ-UI-004 | 貸出処理画面 | DS-UI-004 | 貸出画面設計 |
| RQ-UI-005 | ユーザー管理画面 | DS-UI-005 | ユーザー管理画面設計 |
| RQ-UI-006 | パスワード変更画面 | DS-UI-006 | パスワード変更画面設計 |
| RQ-NF-001 | 利用規模 | DS-PERF-001 | 同時接続対応設計 |
| RQ-NF-002 | 環境要件 | DS-ARC-001, DS-ARC-002 | システムアーキテクチャ |
| RQ-NF-003 | セキュリティ要件 | DS-SEC-001～004 | セキュリティ設計 |
| RQ-NF-004 | ログ・バックアップ | （設計不要） | 実装不要（要件で不要と定義） |

---

## 11. まとめ

本詳細設計書は、要件定義書の全要件をMVP範囲内で矛盾なく実装するための設計を定義しています。

- **DB**: 4テーブル（users, equipments, loans, sessions）
- **API**: 12エンドポイント（認証3、備品2、貸出2、ユーザー4、セッション1）
- **画面**: 6画面（ログイン、備品一覧、備品登録、貸出、ユーザー管理、パスワード変更）
- **セキュリティ**: セッションベース認証、権限チェック、入力検証、エラーハンドリング

全ての設計要素にDS-*IDが付与され、要件との対応が明確です。

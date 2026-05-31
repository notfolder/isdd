# 実装タスク一覧 — 備品管理アプリ

設計書: docs/detail_design.md  
要件書: docs/requirements.md

---

## 1. プロジェクト基盤セットアップ

### 1-1. ディレクトリ構成の作成
- `backend/app/`, `backend/tests/`, `frontend/src/`, `e2e/`, `nginx/` を作成する
- 完了条件: 設計書7章のディレクトリ構成通りに作成されていること

### 1-2. Docker Compose設定
- `docker-compose.yml` を作成し nginx / backend / test_playwright サービスを定義する
- nginx は port 80 で受け、`/api/` を backend にプロキシ、それ以外を Vue ビルド成果物に向ける
- test_playwright はプロファイル `test` のみで起動する構成にする
- 完了条件: `docker compose up` で nginx と backend が起動し、ブラウザで `http://localhost` にアクセスできること

### 1-3. Nginx設定
- `nginx/nginx.conf` を作成し `/api/` リバースプロキシと静的配信を設定する
- 完了条件: フロントエンドが表示され、API呼び出しが通ること

---

## 2. バックエンド実装（FastAPI）

### 2-1. DB接続・モデル定義（DS-SC-EQUIPMENT-DT-ENTITY-EQUIPMENT / DS-SC-USER-DT-ENTITY-USER / DS-SC-LENDING-DT-ENTITY-LENDING）
- `backend/app/database.py`: SQLite接続とセッション生成
- `backend/app/models/equipment.py`: equipment テーブルモデル
- `backend/app/models/user.py`: users テーブルモデル（role check制約含む）
- `backend/app/models/lending.py`: lending_records テーブルモデル（UNIQUE制約含む）
- 完了条件: `docker compose up backend` でテーブルが自動作成されること

### 2-2. 初期管理者シード
- バックエンド起動時、admin ユーザーが0件の場合に環境変数 `INITIAL_ADMIN_PASSWORD` を用いて初期管理者（admin@example.com）を自動登録する
- 完了条件: 初回起動後 admin@example.com でログインできること

### 2-3. 認証実装（DS-CL-AUTH-SERVICE-FT-LOGIN / DS-FN-HASH-PASSWORD-NF-PASSWORD-HASH / DS-FN-CHECK-ROLE-NF-ROLE-CONTROL）
- `backend/app/core/security.py`: bcryptパスワード検証、JWT生成（HS256・有効期限8時間）
- `backend/app/core/deps.py`: 認証済みユーザー取得 Depends 関数、ロール確認 Depends 関数
- `backend/app/services/auth_service.py`: AuthService クラス（login / verify_password / require_role）
- `backend/app/api/auth.py`: POST /api/auth/login エンドポイント
- バリデーション: email 未入力・password 未入力で 422、認証失敗で 401
- 完了条件: 正しいメール/パスワードで JWT トークンが返却されること。誤認証で 401 が返ること

### 2-4. 備品CRUD実装（DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT）
- `backend/app/services/equipment_service.py`: EquipmentService クラス（list_all / create / update / delete）
- `backend/app/api/equipment.py`:
  - GET /api/equipment（全ユーザー）
  - POST /api/equipment（admin のみ）
  - PUT /api/equipment/{management_number}（admin のみ）
  - DELETE /api/equipment/{management_number}（admin のみ）
- 削除バリデーション: 貸出中の備品削除時に 409 を返す
- 管理番号重複時に 409 を返す
- 完了条件: 各エンドポイントが正常系・異常系で仕様通りに動作すること

### 2-5. 貸出・返却実装（DS-FN-RECORD-LENDING-FT-RECORD-LENDING / DS-FN-RECORD-RETURN-FT-RECORD-RETURN）
- `backend/app/services/equipment_service.py` に record_lend / record_return を追加
- POST /api/equipment/{management_number}/lend（admin のみ）
- POST /api/equipment/{management_number}/return（admin のみ）
- 貸出時バリデーション: 既に貸出中の場合 409、返却予定日 < 貸出日の場合 422
- 完了条件: 貸出→返却後に備品状態が「在庫中」に戻ること

### 2-6. ユーザーCRUD実装（DS-CL-USER-SERVICE-FT-MANAGE-USERS）
- `backend/app/services/user_service.py`: UserService クラス
- `backend/app/api/users.py`:
  - GET /api/users（admin のみ）
  - POST /api/users（admin のみ）
  - PUT /api/users/{id}（admin のみ）
  - DELETE /api/users/{id}（admin のみ）
- 削除バリデーション: 貸出中備品があるユーザー削除時に 409 を返す
- メールアドレス重複時に 409 を返す
- 完了条件: 各エンドポイントが正常系・異常系で仕様通りに動作すること

### 2-7. バックエンドテスト（pytest）
- `backend/tests/test_auth.py`: 認証正常系・異常系
- `backend/tests/test_equipment.py`: 備品CRUD + 貸出返却 + 削除制約
- `backend/tests/test_users.py`: ユーザーCRUD + 削除制約
- 完了条件: `pytest` で全テストが PASS すること

---

## 3. フロントエンド実装（Vue + Vuetify）

### 3-1. プロジェクト初期化
- `frontend/` に Vue 3 + Vuetify 3 + Pinia + Vue Router をセットアップする
- マルチステージ Dockerfile を作成し、ビルド成果物を nginx に渡す構成にする
- 完了条件: `docker compose up` でログイン画面が表示されること

### 3-2. 認証・ルーティング実装（DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN / DS-FN-CHECK-ROLE-NF-ROLE-CONTROL）
- `frontend/src/stores/auth.js`: JWT 保存・ロール管理（Pinia）
- `frontend/src/router/index.js`: Vue Router ガード（admin 専用ルートへの一般ユーザーアクセスを 403 リダイレクト）
- `frontend/src/views/LoginView.vue`: メール/パスワードフォーム・エラー表示
- `frontend/src/api/auth.js`: POST /api/auth/login 呼び出し
- 完了条件: 一般ユーザーで管理者専用ページに直接アクセスしてもリダイレクトされること

### 3-3. 備品一覧画面（DS-CL-EQUIPMENT-LIST-VIEW-UI-EQUIPMENT-LIST-SCREEN / DS-CL-LENDING-MODAL-UI-LENDING-MODAL / DS-CL-RETURN-DIALOG-UI-RETURN-DIALOG）
- `frontend/src/views/EquipmentListView.vue`: 全件表示テーブル、管理者向け操作ボタン（貸出/返却/削除）
- `frontend/src/components/LendingModal.vue`: 貸出処理モーダル（ユーザードロップダウン・日付入力・バリデーション）
- `frontend/src/components/ReturnDialog.vue`: 返却確認ダイアログ
- 完了条件: 管理者で貸出→返却を操作すると状態が正しく切り替わること。一般社員には操作ボタンが非表示であること

### 3-4. 備品登録・編集画面（DS-CL-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN）
- `frontend/src/views/EquipmentFormView.vue`: 管理番号・備品名入力フォーム・バリデーション表示
- 完了条件: 登録後に一覧に反映されること。管理番号重複でエラーが表示されること

### 3-5. ユーザー管理画面（DS-CL-USER-LIST-VIEW-UI-USER-LIST-SCREEN / DS-CL-USER-FORM-VIEW-UI-USER-FORM-SCREEN）
- `frontend/src/views/UserListView.vue`: ユーザー一覧・追加・編集・削除
- `frontend/src/views/UserFormView.vue`: 氏名・メール・パスワード・権限フォーム
- 完了条件: ユーザー登録後にそのアカウントでログインできること。貸出中ユーザーの削除でエラーが表示されること

---

## 4. E2Eテスト実装（Playwright）

### 4-1. E2Eテスト環境セットアップ
- `e2e/package.json`, `e2e/playwright.config.js` を作成する
- テスト対象URL を `http://nginx`（docker compose 内サービス名）にする
- 完了条件: `docker compose run --rm test_playwright sh -c "npm install && npx playwright test"` でテストが起動すること

### 4-2. E2Eテストケース実装（DS-FN-E2E-VERIFY-LOGIN-TS-VERIFY-LOGIN 〜 DS-FN-E2E-VERIFY-GENERAL-READONLY-TS-VERIFY-GENERAL-READONLY）

以下の 9 シナリオを実装する:

| シナリオID | テスト目的 |
|---|---|
| RQ-TS-VERIFY-LOGIN | ログイン成功確認 |
| RQ-TS-VERIFY-LOGIN-FAIL | ログイン失敗確認 |
| RQ-TS-VERIFY-EQUIPMENT-LIST | 備品一覧表示確認 |
| RQ-TS-VERIFY-CREATE-EQUIPMENT | 備品登録確認 |
| RQ-TS-VERIFY-LENDING | 貸出処理確認 |
| RQ-TS-VERIFY-RETURN | 返却処理確認 |
| RQ-TS-VERIFY-DELETE-LENT-EQUIPMENT | 貸出中備品削除不可確認 |
| RQ-TS-VERIFY-USER-MANAGE | ユーザー登録確認 |
| RQ-TS-VERIFY-GENERAL-READONLY | 一般社員の権限確認 |

- 完了条件: 全9シナリオが PASS すること

---

## 5. 必須固定タスク

### 5-1. docker compose 起動確認
- `docker-compose.yml` が存在し、`docker compose up` で全サービスが起動することを確認する
- 完了条件: 全サービスが起動ログを出力し、エラーなく立ち上がること

### 5-2. E2Eテスト全件通過
- `e2e/` 配下のテストを全件実行し、全件通過を確認する
- 実行コマンド: `docker compose run --rm test_playwright sh -c "npm install && npx playwright test"`
- 完了条件: テスト結果に FAIL が0件であること。失敗した場合は修正と再実行を繰り返し全件通過まで継続する

### 5-3. README.md 起動方法・初期ユーザー記載
- README.md に「起動方法」セクションと「初期ユーザー」情報を記載する
- 完了条件: README.md を読むだけで初回起動から初期ログイン（admin@example.com）まで完結できること

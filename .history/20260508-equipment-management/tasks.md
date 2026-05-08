# 実装タスク一覧 — 備品管理・貸出管理アプリ

## 凡例

- 完了条件：各タスクが「完了」とみなされる検証可能な条件
- バリデーション：実装後に必ず実行する検証手順

---

## 0. プロジェクト初期化

### Task-0-1: リポジトリ構成とディレクトリ作成

- `backend/app/api/v1/`、`backend/app/core/`、`backend/app/db/`、`backend/app/models/`、`backend/app/schemas/`、`backend/app/services/`、`backend/tests/unit/`、`backend/tests/integration/`
- `frontend/src/api/`、`frontend/src/pages/`、`frontend/src/router/`、`frontend/src/stores/`
- `e2e/tests/`、`nginx/` を作成する
- **完了条件**：設計書 7-1 のディレクトリ構成と一致していること

### Task-0-2: 依存パッケージ定義

- `backend/requirements.txt` に FastAPI、uvicorn、SQLAlchemy、python-jose、passlib[bcrypt]、python-multipart を記載する
- `frontend/package.json` に Vue 3、Vuetify 3、Pinia、Vue Router、Axios を記載する
- `e2e/package.json` に Playwright を記載する
- **完了条件**：`pip install -r requirements.txt` と `npm install` がエラーなく完了すること

---

## 1. データベース設計の実装（DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY, DS-SC-LOAN-DT-LOAN-ENTITY, DS-SC-USER-DT-USER-ENTITY, DS-SC-DB-INIT-DT-DB-REQUIRED）

### Task-1-1: SQLAlchemy モデル実装

- `app/models/equipment.py`：equipment テーブル（id, asset_number UNIQUE, name, status CHECK）
- `app/models/loan.py`：loans テーブル（id, equipment_id FK, user_id FK, lent_at, returned_at NULL）
- `app/models/user.py`：users テーブル（id, username, login_id UNIQUE, password_hash, role CHECK）
- **完了条件**：3 テーブルが設計書 3-1 のカラム・制約どおりに定義されていること

### Task-1-2: DB 初期化・WAL モード設定（DS-FN-CONFIGURE-DB-NF-CONCURRENT-USERS, DS-SC-DB-INIT-DT-DB-REQUIRED）

- `app/db/database.py`：SQLAlchemy セッション管理、起動時に `PRAGMA journal_mode=WAL` を実行する
- `app/main.py`：アプリ起動時に `create_all()` を呼び出す
- **完了条件**：アプリ起動後に `app.db` が生成され `PRAGMA journal_mode` が `wal` を返すこと

### Task-1-3: 初期管理者シード（DS-FN-SEED-INITIAL-USER-FT-CREATE-USER）

- `app/db/seed.py`：login_id が `admin` のユーザーが未存在の場合のみ INSERT する
- **完了条件**：初回起動後に管理者アカウントが 1 件登録されていること。2 回目の起動で重複登録されないこと

### Task-1-4: バリデーション

- `pytest tests/unit/test_models.py` で各モデルのカラム制約（UNIQUE・CHECK）が機能することを検証する
- **完了条件**：全テスト PASS

---

## 2. セキュリティ基盤実装（DS-FN-HASH-PASSWORD-NF-SECURITY-PASSWORD, DS-FN-VERIFY-JWT-NF-SECURITY-ROLE, DS-FN-REQUIRE-ADMIN-NF-SECURITY-ROLE）

### Task-2-1: SecurityHelper 実装

- `app/core/security.py` に `hash_password`、`verify_password`（bcrypt）、`create_jwt`（python-jose）、`verify_jwt` を実装する
- **完了条件**：ハッシュ化・検証・JWT 生成・検証が正常に動作すること

### Task-2-2: 依存注入（deps.py）実装（DS-FN-REQUIRE-ADMIN-NF-SECURITY-ROLE）

- `app/api/deps.py` に `get_current_user`（JWT 検証）と `require_admin`（role チェック）を実装する
- **完了条件**：無効トークンは 401、一般ユーザーで管理者エンドポイントにアクセスすると 403 が返ること

### Task-2-3: バリデーション

- `pytest tests/unit/test_security.py` で `hash_password`/`verify_password`/`create_jwt`/`verify_jwt` の正常系・異常系を検証する
- **完了条件**：全テスト PASS

---

## 3. Pydantic スキーマ実装

### Task-3-1: 備品スキーマ（DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY）

- `app/schemas/equipment.py`：`EquipmentCreate`（asset_number, name）、`EquipmentUpdate`（name）、`EquipmentResponse`（id, asset_number, name, status, borrower_name, lent_at）
- **完了条件**：スキーマが設計書の入出力仕様と一致すること

### Task-3-2: 貸出スキーマ（DS-SC-LOAN-DT-LOAN-ENTITY）

- `app/schemas/loan.py`：`LoanCreate`（equipment_id, user_id）、`LoanResponse`（id, equipment_id, user_id, lent_at, returned_at）
- **完了条件**：スキーマが設計書の入出力仕様と一致すること

### Task-3-3: ユーザースキーマ（DS-SC-USER-DT-USER-ENTITY）

- `app/schemas/user.py`：`UserCreate`（username, login_id, password, role）、`UserUpdate`（username, login_id, password, role）、`UserResponse`（id, username, login_id, role。password_hash は含まない）
- **完了条件**：UserResponse にパスワード情報が含まれないこと

---

## 4. サービスクラス実装

### Task-4-1: AuthService 実装（DS-CL-AUTH-SERVICE-FT-LOGIN, DS-FN-LOGIN-FT-LOGIN）

- `app/services/auth_service.py` に `login`（login_id + password 検証 → JWT 返却）、`get_current_user` を実装する
- **完了条件**：正しい認証情報でトークンが返ること。誤ったパスワードで 401 が発生すること

### Task-4-2: EquipmentService 実装（DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT, DS-FN-CHECK-EQUIPMENT-DELETABLE-FT-DELETE-EQUIPMENT）

- `app/services/equipment_service.py` に `list_all`、`create`（重複 asset_number は 409）、`update`（未存在は 404）、`delete`（貸出中は 409）を実装する
- **完了条件**：設計書 5-2 の各メソッドが業務制約を正しく適用すること

### Task-4-3: LoanService 実装（DS-CL-LOAN-SERVICE-FT-LEND-EQUIPMENT, DS-FN-LEND-FT-LEND-EQUIPMENT）

- `app/services/loan_service.py` に `lend`（トランザクション：loans INSERT + equipment.status = 'lent'）、`return_equipment`（トランザクション：loans.returned_at 記録 + equipment.status = 'available'）を実装する
- **完了条件**：貸出・返却が各々 1 トランザクションで実行されること。DB 更新失敗時にロールバックされること

### Task-4-4: UserService 実装（DS-CL-USER-SERVICE-FT-CREATE-USER, DS-FN-CHECK-USER-DELETABLE-FT-DELETE-USER）

- `app/services/user_service.py` に `list_all`、`create`（重複 login_id は 409、パスワードはハッシュ化）、`update`、`delete`（未返却貸出ありは 409）を実装する
- **完了条件**：設計書 5-2 の各メソッドが業務制約を正しく適用すること

### Task-4-5: 単体テスト

- `backend/tests/unit/` 配下に各サービスの単体テストを実装する（設計書 8-2 の全テストケースを網羅）
- **完了条件**：`pytest tests/unit/` が全件 PASS

---

## 5. API エンドポイント実装

### Task-5-1: 認証エンドポイント（DS-IF-AUTH-LOGIN-FT-LOGIN, DS-IF-AUTH-LOGOUT-FT-LOGOUT）

- `app/api/v1/auth.py`：`POST /api/auth/login`（TokenResponse を返す）、`POST /api/auth/logout`（フロントエンド側でトークン削除するため 200 OK を返すのみ）を実装する
- **完了条件**：正しい認証情報で 200 + トークン返却。誤った認証情報で 401 返却

### Task-5-2: 備品エンドポイント（DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT, DS-IF-CREATE-EQUIPMENT-FT-CREATE-EQUIPMENT, DS-IF-UPDATE-EQUIPMENT-FT-EDIT-EQUIPMENT, DS-IF-DELETE-EQUIPMENT-FT-DELETE-EQUIPMENT）

- `app/api/v1/equipment.py`：`GET /api/equipment`（全員）、`POST /api/equipment`（管理者のみ）、`PUT /api/equipment/{id}`（管理者のみ）、`DELETE /api/equipment/{id}`（管理者のみ）を実装する
- 全エンドポイントに `/api/` プレフィックスを統一する
- **完了条件**：設計書 6-1 のエラー仕様どおりのレスポンスが返ること

### Task-5-3: 貸出エンドポイント（DS-IF-LEND-EQUIPMENT-FT-LEND-EQUIPMENT, DS-IF-RETURN-EQUIPMENT-FT-RETURN-EQUIPMENT）

- `app/api/v1/loans.py`：`POST /api/loans`（管理者のみ）、`PUT /api/loans/{id}/return`（管理者のみ）を実装する
- **完了条件**：貸出後に備品の status が 'lent' に変わること。返却後に 'available' に戻ること

### Task-5-4: ユーザーエンドポイント（DS-IF-LIST-USERS-FT-DELETE-USER, DS-IF-CREATE-USER-FT-CREATE-USER, DS-IF-UPDATE-USER-FT-EDIT-USER, DS-IF-DELETE-USER-FT-DELETE-USER）

- `app/api/v1/users.py`：`GET /api/users`（管理者のみ）、`POST /api/users`（管理者のみ）、`PUT /api/users/{id}`（管理者のみ）、`DELETE /api/users/{id}`（管理者のみ）を実装する
- **完了条件**：一般ユーザーがアクセスすると 403 が返ること

### Task-5-5: 結合テスト・総合テスト

- `backend/tests/integration/` と `backend/tests/` 配下に設計書 8-3・8-4 の全テストケースを実装する
- **完了条件**：`pytest tests/` が全件 PASS

---

## 6. フロントエンド実装

### Task-6-1: Axios クライアント（DS-MD-API-CLIENT-FT-LIST-EQUIPMENT）

- `src/api/client.js`：Bearer トークン自動付与・401 時のログイン画面リダイレクトを実装する
- **完了条件**：全 API 呼び出しが `src/api/client.js` 経由で行われること

### Task-6-2: 認証ストア（DS-MD-AUTH-STORE-FT-LOGIN）

- `src/stores/auth.js`（Pinia）：`login`（トークン・役割を localStorage に保存）、`logout`（localStorage をクリア）、`isAdmin` 算出プロパティを実装する
- **完了条件**：ログイン後に isAdmin が正しい値を返すこと

### Task-6-3: Vue Router 設定（DS-FN-REQUIRE-ADMIN-NF-SECURITY-ROLE）

- `src/router/index.js`：未ログイン時はログイン画面にリダイレクト、一般ユーザーが管理者専用ルートにアクセスした場合は備品一覧にリダイレクトするナビゲーションガードを設定する
- **完了条件**：一般ユーザーがユーザー管理ページの URL を直接入力しても遷移しないこと

### Task-6-4: ログイン画面（DS-MD-LOGIN-PAGE-UI-LOGIN-SCREEN）

- `src/pages/LoginPage.vue`：ログインID・パスワードフォーム、ログインボタン、エラーメッセージ表示を実装する
- **完了条件**：設計書 4-1 の AA モックアップと一致すること

### Task-6-5: 備品一覧画面（DS-MD-EQUIPMENT-LIST-PAGE-UI-EQUIPMENT-LIST-SCREEN）

- `src/pages/EquipmentListPage.vue`：管理者ビュー（貸出先・貸出日・操作ボタン表示）と一般ユーザービュー（状態のみ表示）を役割に応じて切り替える
- **完了条件**：設計書 4-1 の各 AA モックアップと一致すること

### Task-6-6: 備品登録・編集画面（DS-MD-EQUIPMENT-FORM-PAGE-UI-EQUIPMENT-FORM-SCREEN）

- `src/pages/EquipmentFormPage.vue`：新規登録と編集を props で切り替え、保存・キャンセルを実装する
- **完了条件**：バリデーションエラーがフォーム下に表示されること

### Task-6-7: 貸出登録画面（DS-MD-LEND-PAGE-UI-LEND-SCREEN）

- `src/pages/LendPage.vue`：備品名・資産管理番号表示、ユーザー一覧プルダウン、貸出確定・キャンセルを実装する
- **完了条件**：設計書 4-1 の AA モックアップと一致すること

### Task-6-8: ユーザー管理・登録編集画面（DS-MD-USER-MANAGEMENT-PAGE-UI-USER-MANAGEMENT-SCREEN, DS-MD-USER-FORM-PAGE-UI-USER-FORM-SCREEN）

- `src/pages/UserManagementPage.vue`：ユーザー一覧・削除確認ダイアログを実装する
- `src/pages/UserFormPage.vue`：新規登録と編集を props で切り替えて実装する
- **完了条件**：設計書 4-1 の AA モックアップと一致すること

---

## 7. Nginx・Docker 設定

### Task-7-1: Nginx 設定

- `nginx/nginx.conf`：`/` は Vue 静的ファイルを配信、`/api/` は `http://backend:8000` にプロキシする設定を記述する
- **完了条件**：`curl http://localhost/` が Vue の HTML を返すこと。`curl http://localhost/api/equipment` が FastAPI のレスポンスを返すこと

### Task-7-2: Dockerfile 作成

- `backend/Dockerfile`：Python イメージ + pip install + uvicorn 起動
- `frontend/Dockerfile`：Node.js ビルドステージ + Nginx 配信ステージのマルチステージビルド
- **完了条件**：`docker build` がエラーなく完了すること

### Task-7-3: docker-compose.yml 作成

- `nginx`、`backend`、`test_playwright`（profile: test）の 3 サービスを定義する
- SQLite ファイルを `backend` コンテナのボリュームでホストに永続化する
- **完了条件**：`docker compose up` で全サービスが起動し `http://localhost/` にアクセスできること

---

## 8. E2E テスト実装

### Task-8-1: E2E テスト設定

- `e2e/playwright.config.js`：baseURL を `http://nginx/` に設定する
- **完了条件**：`docker compose run --rm test_playwright sh -c "npm install && npx playwright test --list"` がテスト一覧を出力すること

### Task-8-2: 認証 E2E テスト（DS-MD-E2E-LOGIN-SUCCESS-TS-LOGIN-SUCCESS, DS-MD-E2E-LOGIN-FAIL-TS-LOGIN-FAIL）

- `e2e/tests/auth.spec.js` に RQ-TS-LOGIN-SUCCESS、RQ-TS-LOGIN-FAIL のシナリオを実装する
- **完了条件**：`npx playwright test auth.spec.js` が全件 PASS

### Task-8-3: 備品 E2E テスト（DS-MD-E2E-CREATE-EQUIPMENT-TS-CREATE-EQUIPMENT, DS-MD-E2E-EDIT-EQUIPMENT-TS-EDIT-EQUIPMENT, DS-MD-E2E-DELETE-EQUIPMENT-OK-TS-DELETE-EQUIPMENT-OK, DS-MD-E2E-DELETE-EQUIPMENT-NG-TS-DELETE-EQUIPMENT-NG）

- `e2e/tests/equipment.spec.js` に RQ-TS-CREATE-EQUIPMENT、RQ-TS-EDIT-EQUIPMENT、RQ-TS-DELETE-EQUIPMENT-OK、RQ-TS-DELETE-EQUIPMENT-NG のシナリオを実装する
- **完了条件**：`npx playwright test equipment.spec.js` が全件 PASS

### Task-8-4: 貸出・返却 E2E テスト（DS-MD-E2E-LEND-EQUIPMENT-TS-LEND-EQUIPMENT, DS-MD-E2E-RETURN-EQUIPMENT-TS-RETURN-EQUIPMENT）

- `e2e/tests/loan.spec.js` に RQ-TS-LEND-EQUIPMENT、RQ-TS-RETURN-EQUIPMENT のシナリオを実装する
- **完了条件**：`npx playwright test loan.spec.js` が全件 PASS

### Task-8-5: 一般ユーザー E2E テスト（DS-MD-E2E-GENERAL-USER-VIEW-TS-GENERAL-USER-VIEW）

- `e2e/tests/general-user.spec.js` に RQ-TS-GENERAL-USER-VIEW のシナリオを実装する
- **完了条件**：操作ボタンが DOM 上に存在しないことを検証していること

### Task-8-6: ユーザー管理 E2E テスト（DS-MD-E2E-CREATE-USER-TS-CREATE-USER, DS-MD-E2E-DELETE-USER-NG-TS-DELETE-USER-NG, DS-MD-E2E-DELETE-USER-OK-TS-DELETE-USER-OK）

- `e2e/tests/user.spec.js` に RQ-TS-CREATE-USER、RQ-TS-DELETE-USER-NG、RQ-TS-DELETE-USER-OK のシナリオを実装する
- **完了条件**：`npx playwright test user.spec.js` が全件 PASS

---

## 9. README 作成

### Task-9-1: README.md 作成

- プロジェクトルートに `README.md` を作成する。起動方法（`docker compose up`）、初期ログイン情報（login_id: admin）、各画面の操作説明を記載する
- **完了条件**：README の手順どおりに起動・ログインできること

---

## 10. 全体確認

### Task-10-1: 実装完了チェック

以下を全て確認すること。

- [ ] `pytest tests/` が全件 PASS（バックエンド単体・結合・総合テスト）
- [ ] `docker compose run --rm test_playwright sh -c "npm install && npx playwright test"` が全件 PASS（E2E テスト 12 シナリオ）
- [ ] `docker compose up` で正常起動し `http://localhost/` にアクセスできること
- [ ] 管理者アカウント（login_id: admin）でログインし全機能が動作すること
- [ ] 一般ユーザーアカウントでログインし閲覧のみ可能で操作ボタンが表示されないこと
- [ ] `python3 .agents/skills/isdd-common/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が全件合格であること

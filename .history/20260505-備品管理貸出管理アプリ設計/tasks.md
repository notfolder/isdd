# 実装タスク一覧

対象設計書: docs/detail_design.md
対象要件書: docs/requirements.md

---

## タスク一覧

### T01: プロジェクト基盤構築

**完了条件**: docker compose up -d で frontend・backend の両サービスが起動し、ブラウザで http://localhost にアクセスして Vue3 の初期画面が表示される。

- [ ] docker-compose.yml を作成する（frontend・backend サービス、SQLite ボリューム定義）
- [ ] backend/Dockerfile を作成する（Python 3.12 + uvicorn マルチステージビルド）
- [ ] frontend/Dockerfile を作成する（Vue3 マルチステージビルド + Nginx 配信）
- [ ] frontend/nginx.conf を作成する（/api/ を backend:8000 へプロキシ）
- [ ] .env.example を作成する（INITIAL_ADMIN_LOGIN_ID・INITIAL_ADMIN_PASSWORD・JWT_SECRET_KEY）
- [ ] **バリデーション**: docker compose up -d を実行し、http://localhost にアクセスして 200 が返ることを確認する

---

### T02: バックエンド DB・ORM 基盤実装

**完了条件**: SQLAlchemy の create_all で equipment・user・loan_state テーブルが自動作成される。

- [ ] backend/app/core/database.py を実装する（SQLAlchemy エンジン・セッション生成、SQLite ファイルパス設定）
- [ ] backend/app/models/equipment.py を実装する（equipment テーブル ORM モデル）
- [ ] backend/app/models/user.py を実装する（user テーブル ORM モデル）
- [ ] backend/app/models/loan_state.py を実装する（loan_state テーブル ORM モデル、FK 制約）
- [ ] backend/app/main.py に startup イベントで create_all を呼び出す処理を実装する
- [ ] **バリデーション**: backend コンテナ起動後、app.db に 3 テーブルが存在することを確認する

---

### T03: バックエンド Repository 層実装

**完了条件**: 各 Repository の全メソッドが pytest 単体テストで正常系・異常系ともにパスする。

- [ ] backend/app/repositories/equipment.py を実装する（find_all / find_by_id / create / update / delete）
- [ ] backend/app/repositories/user.py を実装する（find_all / find_by_login_id / count_admins / create / update / delete）
- [ ] backend/app/repositories/loan_state.py を実装する（find_by_equipment_id / create / delete_by_equipment_id / exists_by_user_login_id）
- [ ] **バリデーション**: pytest tests/unit/test_repositories.py を実行して全テストがパスすることを確認する

---

### T04: バックエンド 認証基盤実装（DS-CL-AUTH-SERVICE-FT-LOGIN）

**完了条件**: DS-FN-TEST-AUTH-AUTHENTICATE-FT-LOGIN・DS-FN-TEST-AUTH-TOKEN-FT-LOGIN の単体テストが全てパスする。初期管理者がログインできる。

- [ ] backend/app/core/config.py を実装する（環境変数 JWT_SECRET_KEY 読み込み）
- [ ] backend/app/core/auth.py を実装する（JWT 生成・検証・Depends 関数 get_current_user / require_admin）
- [ ] backend/app/services/auth_service.py を実装する（authenticate / create_token / verify_token）
- [ ] backend/app/api/auth.py を実装する（POST /api/auth/login・POST /api/auth/logout）
- [ ] **バリデーション**: pytest tests/unit/test_auth_service.py と tests/integration/test_api_auth.py を実行して全テストがパスすることを確認する

---

### T05: バックエンド 初期管理者作成実装（DS-FN-INIT-ADMIN-OP-INITIAL-ADMIN-ENV）

**完了条件**: DS-FN-TEST-INIT-ADMIN-OP-INITIAL-ADMIN-ENV の単体テストがパスする。環境変数設定後の初回起動で管理者利用者が作成される。

- [ ] backend/app/services/user_service.py に initialize_admin メソッドを実装する（user テーブルが空の場合のみ作成）
- [ ] backend/app/main.py の startup イベントで initialize_admin を呼び出す処理を実装する
- [ ] **バリデーション**: pytest tests/unit/test_user_service.py::test_init_admin を実行してパスすることを確認する。docker compose up 後に環境変数の ID/PW でログインできることを確認する

---

### T06: バックエンド UserService・UserRouter 実装（DS-CL-USER-SERVICE-FT-MANAGE-BORROWER）

**完了条件**: DS-FN-TEST-USER-CREATE・DELETE・LAST-ADMIN 単体テストと DS-FN-TEST-API-USER-CRUD 結合テストが全てパスする。

- [ ] backend/app/services/user_service.py の全メソッドを実装する（list_users / create / update / delete / get_users_for_loan）
  - 最後の管理者の role 変更制限
  - 自分自身・最後の管理者・貸出中貸出先の削除制限
  - パスワードの bcrypt ハッシュ化
- [ ] backend/app/schemas/user.py を実装する（UserCreate / UserUpdate / UserResponse Pydantic モデル）
- [ ] backend/app/api/users.py を実装する（GET/POST/PUT/DELETE /api/users）
- [ ] **バリデーション**: pytest tests/unit/test_user_service.py と tests/integration/test_api_users.py を実行して全テストがパスすることを確認する

---

### T07: バックエンド EquipmentService・EquipmentRouter 実装（DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT）

**完了条件**: DS-FN-TEST-EQUIPMENT-* 単体テストと DS-FN-TEST-API-EQUIPMENT-* 結合テストが全てパスする。

- [ ] backend/app/services/equipment_service.py の全メソッドを実装する（list_equipment / create / update / delete / loan / return_equipment）
  - 貸出中備品の削除制限
  - 貸出済み備品への再貸出制限
  - loan と return のトランザクション処理（DS-FN-TRANSACTION-LOAN / RETURN）
- [ ] backend/app/schemas/equipment.py を実装する（EquipmentCreate / EquipmentUpdate / EquipmentResponse）
- [ ] backend/app/schemas/loan.py を実装する（LoanCreate）
- [ ] backend/app/api/equipment.py を実装する（GET/POST/PUT/DELETE /api/equipment、POST /api/equipment/{id}/loan・return）
- [ ] **バリデーション**: pytest tests/unit/test_equipment_service.py と tests/integration/test_api_equipment.py を実行して全テストがパスすることを確認する

---

### T08: フロントエンド API クライアントと Pinia ストア実装

**完了条件**: ApiClient の 401 インターセプターが機能し、axios 呼び出しが全て api/ 配下の関数経由になっている。

- [ ] frontend/src/api/client.js を実装する（axios 共通設定・401 インターセプター → /login へリダイレクト）
- [ ] frontend/src/api/auth.js を実装する（login / logout）
- [ ] frontend/src/api/equipment.js を実装する（list / create / update / delete / loan / return）
- [ ] frontend/src/api/users.js を実装する（list / create / update / delete）
- [ ] frontend/src/stores/auth.js を実装する（AuthStore: ログイン状態・ロール・errorMessage）
- [ ] frontend/src/stores/equipment.js を実装する（EquipmentStore: 備品一覧データ）
- [ ] frontend/src/stores/user.js を実装する（UserStore: 利用者一覧データ）
- [ ] frontend/src/router/index.js を実装する（ログインガード・ロール別ルート 13 パターン）
- [ ] **バリデーション**: 未ログイン状態でブラウザから /admin/equipment にアクセスすると /login にリダイレクトされることを確認する

---

### T09: フロントエンド ログイン・ログアウト画面実装（DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN）

**完了条件**: E2E シナリオ DS-FN-E2E-ADMIN-LOGIN・DS-FN-E2E-GENERAL-LOGIN がパスする。

- [ ] frontend/src/views/LoginView.vue を実装する（ログインID・パスワード入力・ログインボタン・エラー表示）
- [ ] **バリデーション**: ブラウザでログイン画面を開き、正しい ID/PW でログインすると role に応じた画面に遷移することを確認する。誤り ID/PW でエラーメッセージが表示されることを確認する

---

### T10: フロントエンド 管理者向け備品一覧画面実装（DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN）

**完了条件**: 備品一覧に備品ID・備品名・状態・貸出先（貸出中の場合）が表示され、貸出可能備品に貸出・削除ボタン、貸出中備品に返却ボタンが表示される。

- [ ] frontend/src/views/AdminEquipmentListView.vue を実装する（一覧表示・備品登録ボタン・利用者管理ボタン・ログアウトボタン）
- [ ] **バリデーション**: 管理者でログイン後、備品一覧画面で状態と操作ボタンが正しく表示されることをブラウザで確認する

---

### T11: フロントエンド 備品登録・編集・削除画面実装

**完了条件**: E2E シナリオ DS-FN-E2E-EQUIPMENT-MANAGEMENT がパスする。

- [ ] frontend/src/views/EquipmentFormView.vue を実装する（新規登録・編集共用、備品ID は新規のみ入力可）
- [ ] frontend/src/views/EquipmentDeleteConfirmView.vue を実装する（削除対象の確認表示・削除実行）
- [ ] **バリデーション**: 備品の新規登録・編集・削除が一連の操作で正しく機能することをブラウザで確認する。貸出中備品の削除を試みるとエラーが表示されることを確認する

---

### T12: フロントエンド 貸出登録・返却確認画面実装

**完了条件**: E2E シナリオ DS-FN-E2E-LOAN-EQUIPMENT・DS-FN-E2E-RETURN-EQUIPMENT がパスする。

- [ ] frontend/src/views/LoanFormView.vue を実装する（利用者ドロップダウン・貸出日入力・登録ボタン）
- [ ] frontend/src/views/ReturnConfirmView.vue を実装する（貸出情報確認表示・返却実行ボタン）
- [ ] **バリデーション**: 貸出登録後に備品状態が貸出中になり、返却後に貸出可能に戻ることをブラウザで確認する

---

### T13: フロントエンド 利用者管理画面実装

**完了条件**: E2E シナリオ DS-FN-E2E-BORROWER-MANAGEMENT がパスする。

- [ ] frontend/src/views/UserListView.vue を実装する（利用者一覧・パスワード非表示・登録・編集・削除ボタン）
- [ ] frontend/src/views/UserFormView.vue を実装する（新規登録・編集共用、ログインID は新規のみ入力可、パスワード非表示）
- [ ] frontend/src/views/UserDeleteConfirmView.vue を実装する（削除対象の確認表示・削除実行）
- [ ] **バリデーション**: 利用者の登録・権限変更・削除が正しく機能することをブラウザで確認する。制限対象（自分自身・最後の管理者・貸出中貸出先）の削除でエラーが表示されることを確認する

---

### T14: フロントエンド 一般利用者向け備品一覧画面実装（DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN）

**完了条件**: E2E シナリオ DS-FN-E2E-GENERAL-VIEW がパスする。

- [ ] frontend/src/views/GeneralEquipmentListView.vue を実装する（備品ID・備品名・状態の閲覧専用表示・操作ボタン非表示）
- [ ] **バリデーション**: 一般利用者でログイン後、備品一覧に操作ボタンが表示されないことをブラウザで確認する

---

### T15: E2Eテスト実装

**完了条件**: `docker compose run --rm test_playwright sh -c "npm install && npx playwright test"` で全 10 シナリオが通過する。

- [ ] e2e/playwright.config.js を実装する（BASE_URL=http://frontend・タイムアウト設定）
- [ ] e2e/package.json を作成する（playwright 依存関係定義）
- [ ] e2e/tests/auth.spec.js を実装する（DS-FN-E2E-ADMIN-LOGIN・DS-FN-E2E-GENERAL-LOGIN・DS-FN-E2E-INIT-ADMIN・DS-FN-E2E-LOGOUT・DS-FN-E2E-AUTO-LOGOUT）
- [ ] e2e/tests/equipment.spec.js を実装する（DS-FN-E2E-EQUIPMENT-MANAGEMENT・DS-FN-E2E-LOAN-EQUIPMENT・DS-FN-E2E-RETURN-EQUIPMENT）
- [ ] e2e/tests/users.spec.js を実装する（DS-FN-E2E-BORROWER-MANAGEMENT）
- [ ] e2e/tests/general.spec.js を実装する（DS-FN-E2E-GENERAL-VIEW）
- [ ] **バリデーション**: E2E 実行コマンドを実行し、全 10 シナリオが PASSED になることを確認する

---

### T16: README.md 作成と全体確認

**完了条件**: README.md の手順通りに起動でき、全機能が要件定義書の仕様通りに動作することを確認できる。

- [ ] README.md を作成する（.env 設定方法・起動コマンド・E2E テスト実行コマンドを記載）
- [ ] **バリデーション（全体確認）**: 以下を全て確認する
  - docker compose up -d で正常起動する
  - 初期管理者でログインできる
  - 備品の登録・編集・貸出・返却・削除が一連の操作で動作する
  - 利用者の登録・権限変更・削除が動作し、制限が正しく機能する
  - 一般利用者は閲覧のみで操作ボタンが表示されない
  - 60 分非操作後（または E2E の clock.fastForward）で自動ログアウトされる
  - pytest を実行して全単体テスト・結合テストがパスする
  - E2E テストを実行して全 10 シナリオがパスする

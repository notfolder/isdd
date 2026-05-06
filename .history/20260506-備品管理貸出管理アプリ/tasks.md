# 備品管理・貸出管理アプリ 実装タスク一覧

作成日: 2026-05-06  
対応設計書: `docs/detail_design.md`

---

## タスク一覧

### 1. プロジェクト初期化

#### TASK-001: docker-compose.yml 作成
- **内容**: プロジェクトルートに docker-compose.yml を作成し、backend、frontend、e2e の3サービスを定義する
- **対応設計ID**: DS-MD-DOCKER-COMPOSE-DT-DOCKER-COMPOSE
- **完了条件**: 
  - backend サービス（ポート8000公開）が定義されている
  - frontend サービス（ポート5173公開）が定義されている
  - e2e サービス（frontendに依存）が定義されている
  - data ディレクトリがマウントされている
- **バリデーション**: `docker compose config` でエラーが出ないこと

#### TASK-002: data ディレクトリ作成
- **内容**: プロジェクトルートに data ディレクトリを作成する（SQLiteデータベース保存用）
- **対応設計ID**: DS-SC-ITEMS-DT-ITEM, DS-SC-USERS-DT-USER
- **完了条件**: data/ ディレクトリが存在する
- **バリデーション**: `ls data/` でディレクトリが確認できること

---

### 2. バックエンド実装

#### TASK-003: backend プロジェクト初期化
- **内容**: backend/ ディレクトリを作成し、requirements.txt と Dockerfile を作成する
- **対応設計ID**: DS-MD-BACKEND-API-FT-LOGIN
- **完了条件**: 
  - backend/requirements.txt が作成され、fastapi、uvicorn、pyjwt、bcrypt、pytestが含まれている
  - backend/Dockerfile が作成されている
  - backend/src/ ディレクトリ構造が作成されている（database/, services/, routers/, schemas/）
- **バリデーション**: `docker compose build backend` でビルドが成功すること

#### TASK-004: DatabaseManager 実装
- **内容**: backend/src/database/database_manager.py に DatabaseManager クラスを実装する
- **対応設計ID**: DS-CL-DATABASE-MANAGER-DT-DB-REQUIRED
- **完了条件**: 
  - DatabaseManager クラスが実装されている
  - `connect()` メソッドでデータベース接続を行う
  - `initialize()` メソッドで items テーブルと users テーブルを作成する
  - `create_initial_admin()` メソッドで初期管理者（admin/admin）を作成する
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: 単体テストを作成し、テーブル作成と初期データ投入が成功すること

#### TASK-005: schemas.py 実装
- **内容**: backend/src/schemas/schemas.py に Pydantic スキーマを実装する
- **対応設計ID**: DS-CL-SCHEMAS-DT-ITEM
- **完了条件**: 
  - LoginRequest, LoginResponse スキーマが実装されている
  - ItemBase, ItemResponse, ItemCreate, ItemUpdate スキーマが実装されている
  - LendRequest スキーマが実装されている
  - UserBase, UserResponse, UserCreate, UserUpdate スキーマが実装されている
  - 全スキーマに型ヒントとdocstringが付与されている
- **バリデーション**: Pydanticのバリデーションが正しく動作すること（テストで確認）

#### TASK-006: AuthService 実装
- **内容**: backend/src/services/auth_service.py に AuthService クラスを実装する
- **対応設計ID**: DS-CL-AUTH-SERVICE-FT-LOGIN
- **完了条件**: 
  - AuthService クラスが実装されている
  - `hash_password()` メソッドで bcrypt によるパスワードハッシュ化を行う
  - `verify_password()` メソッドでパスワード検証を行う
  - `authenticate()` メソッドでユーザー認証を行う
  - `create_token()` メソッドで JWT トークンを発行する（有効期限: 24時間）
  - `verify_token()` メソッドで JWT トークンを検証する
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: 単体テストを作成し、全メソッドが正しく動作すること

#### TASK-007: ItemService 実装
- **内容**: backend/src/services/item_service.py に ItemService クラスを実装する
- **対応設計ID**: DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM
- **完了条件**: 
  - ItemService クラスが実装されている
  - `get_all_items()` メソッドで全備品を取得する
  - `get_item()` メソッドで備品を1件取得する
  - `create_item()` メソッドで備品を登録する（資産管理番号の重複チェックを行う）
  - `update_item()` メソッドで備品を更新する
  - `delete_item()` メソッドで備品を削除する
  - `lend_item()` メソッドで備品を貸出する（貸出中チェックを行う）
  - `return_item()` メソッドで備品を返却する（貸出中チェックを行う）
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: 単体テストを作成し、全メソッドが正しく動作すること

#### TASK-008: UserService 実装
- **内容**: backend/src/services/user_service.py に UserService クラスを実装する
- **対応設計ID**: DS-CL-USER-SERVICE-FT-REGISTER-USER
- **完了条件**: 
  - UserService クラスが実装されている
  - `get_all_users()` メソッドで全利用者を取得する
  - `get_user()` メソッドで利用者を1件取得する
  - `create_user()` メソッドで利用者を登録する（ユーザーIDの重複チェックを行う）
  - `update_user()` メソッドで利用者を更新する
  - `delete_user()` メソッドで利用者を削除する
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: 単体テストを作成し、全メソッドが正しく動作すること

#### TASK-009: AuthRouter 実装
- **内容**: backend/src/routers/auth_router.py に AuthRouter を実装する
- **対応設計ID**: DS-CL-AUTH-ROUTER-FT-LOGIN
- **完了条件**: 
  - POST /api/auth/login エンドポイントが実装されている
  - リクエストボディで LoginRequest を受け取る
  - AuthService.authenticate() を呼び出して認証を行う
  - 成功時は JWT トークン、ユーザーID、権限を返す
  - 失敗時は 401 Unauthorized を返す
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: 統合テストを作成し、APIが正しく動作すること

#### TASK-010: ItemRouter 実装
- **内容**: backend/src/routers/item_router.py に ItemRouter を実装する
- **対応設計ID**: DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM
- **完了条件**: 
  - GET /api/items エンドポイントが実装されている（JWT認証必須）
  - GET /api/items/{asset_number} エンドポイントが実装されている（JWT認証必須）
  - POST /api/items エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - PUT /api/items/{asset_number} エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - DELETE /api/items/{asset_number} エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - POST /api/items/{asset_number}/lend エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - POST /api/items/{asset_number}/return エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - 全エンドポイントで ItemService のメソッドを呼び出す
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: 統合テストを作成し、全エンドポイントが正しく動作すること

#### TASK-011: UserRouter 実装
- **内容**: backend/src/routers/user_router.py に UserRouter を実装する
- **対応設計ID**: DS-CL-USER-ROUTER-FT-REGISTER-USER
- **完了条件**: 
  - GET /api/users エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - GET /api/users/{user_id} エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - POST /api/users エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - PUT /api/users/{user_id} エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - DELETE /api/users/{user_id} エンドポイントが実装されている（JWT認証必須、管理者のみ）
  - 全エンドポイントで UserService のメソッドを呼び出す
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: 統合テストを作成し、全エンドポイントが正しく動作すること

#### TASK-012: main.py 実装
- **内容**: backend/src/main.py に FastAPI アプリのエントリーポイントを実装する
- **対応設計ID**: DS-MD-BACKEND-API-FT-LOGIN
- **完了条件**: 
  - FastAPI アプリが初期化されている
  - CORS設定（localhost:5173からのアクセスを許可）が行われている
  - DatabaseManager.initialize() を起動時に実行する
  - AuthRouter、ItemRouter、UserRouter がルーターに登録されている
  - PEP8に準拠し、型ヒントとdocstringが付与されている
- **バリデーション**: `docker compose up backend` で起動し、http://localhost:8000/docs にアクセスできること

---

### 3. フロントエンド実装

#### TASK-013: frontend プロジェクト初期化
- **内容**: frontend/ ディレクトリを作成し、Vite + Vue 3 + Vuetify 3 プロジェクトを初期化する
- **対応設計ID**: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN
- **完了条件**: 
  - `npm create vite@latest frontend -- --template vue-ts` でプロジェクトが作成されている
  - Vuetify 3、Vue Router、Pinia がインストールされている
  - frontend/Dockerfile が作成されている
  - frontend/src/ ディレクトリ構造が作成されている（views/, components/, api/, stores/, router/）
- **バリデーション**: `docker compose build frontend` でビルドが成功すること

#### TASK-014: ApiClient 実装
- **内容**: frontend/src/api/apiClient.ts に ApiClient クラスを実装する
- **対応設計ID**: DS-CL-API-CLIENT-FT-LOGIN
- **完了条件**: 
  - ApiClient クラスが実装されている
  - `login()` メソッドで POST /api/auth/login を呼び出す
  - `getItems()` メソッドで GET /api/items を呼び出す
  - `getItem()` メソッドで GET /api/items/{asset_number} を呼び出す
  - `createItem()` メソッドで POST /api/items を呼び出す
  - `updateItem()` メソッドで PUT /api/items/{asset_number} を呼び出す
  - `deleteItem()` メソッドで DELETE /api/items/{asset_number} を呼び出す
  - `lendItem()` メソッドで POST /api/items/{asset_number}/lend を呼び出す
  - `returnItem()` メソッドで POST /api/items/{asset_number}/return を呼び出す
  - `getUsers()` メソッドで GET /api/users を呼び出す
  - `getUser()` メソッドで GET /api/users/{user_id} を呼び出す
  - `createUser()` メソッドで POST /api/users を呼び出す
  - `updateUser()` メソッドで PUT /api/users/{user_id} を呼び出す
  - `deleteUser()` メソッドで DELETE /api/users/{user_id} を呼び出す
  - JWT認証が必要なエンドポイントでは Authorization ヘッダーにトークンを付与する
  - 型定義が明示されている
- **バリデーション**: バックエンドと通信し、各メソッドが正しく動作すること

#### TASK-015: AuthStore 実装
- **内容**: frontend/src/stores/authStore.ts に AuthStore（Pinia）を実装する
- **対応設計ID**: DS-CL-AUTH-STORE-FT-LOGIN
- **完了条件**: 
  - AuthStore が実装されている
  - `token`、`userId`、`role` の状態を管理する
  - `login()` アクションで ApiClient.login() を呼び出し、認証情報を保存する
  - `logout()` アクションで認証情報をクリアする
  - `isAuthenticated()` ゲッターで認証状態を返す
  - `isAdmin()` ゲッターで管理者権限を返す
  - 型定義が明示されている
- **バリデーション**: ログイン・ログアウト処理が正しく動作すること

#### TASK-016: Vue Router 設定
- **内容**: frontend/src/router/index.ts に Vue Router の設定を実装する
- **対応設計ID**: DS-MD-FRONTEND-APP-UI-LOGIN-SCREEN
- **完了条件**: 
  - `/login` ルート（LoginView）が定義されている
  - `/items` ルート（ItemListView）が定義されている
  - `/items/register` ルート（ItemRegisterView）が定義されている
  - `/items/:asset_number/edit` ルート（ItemEditView）が定義されている
  - `/users` ルート（UserListView）が定義されている
  - `/users/register` ルート（UserRegisterView）が定義されている
  - `/users/:user_id/edit` ルート（UserEditView）が定義されている
  - `/lending` ルート（LendingView）が定義されている
  - `/return` ルート（ReturnView）が定義されている
  - 認証ガード（AuthStore.isAuthenticated() でチェック）が設定されている
  - 型定義が明示されている
- **バリデーション**: ルーティングが正しく動作し、未認証時はログイン画面にリダイレクトされること

#### TASK-017: LoginView 実装
- **内容**: frontend/src/views/LoginView.vue にログイン画面を実装する
- **対応設計ID**: DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN
- **完了条件**: 
  - ユーザーID入力フィールドが実装されている
  - パスワード入力フィールドが実装されている
  - ログインボタンが実装されている
  - ログインボタンクリック時に AuthStore.login() を呼び出す
  - ログイン成功時は /items へリダイレクトする
  - ログイン失敗時はエラーメッセージを表示する
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: ログイン画面が表示され、ログイン処理が正しく動作すること

#### TASK-018: ItemListView 実装
- **内容**: frontend/src/views/ItemListView.vue に備品一覧画面を実装する
- **対応設計ID**: DS-CL-ITEM-LIST-VIEW-UI-ITEM-LIST-SCREEN
- **完了条件**: 
  - 備品一覧テーブル（資産管理番号、名称、借り主、ステータス）が実装されている
  - 画面表示時に ApiClient.getItems() を呼び出して備品一覧を取得する
  - 備品登録ボタン（管理者のみ表示）が実装されている
  - 貸出ボタン（管理者のみ表示）が実装されている
  - 返却ボタン（管理者のみ表示）が実装されている
  - 編集ボタン（管理者のみ表示）が実装されている
  - 削除ボタン（管理者のみ表示）が実装されている
  - ログアウトボタンが実装されている
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 備品一覧が表示され、各ボタンが正しく動作すること

#### TASK-019: ItemRegisterView 実装
- **内容**: frontend/src/views/ItemRegisterView.vue に備品登録画面を実装する
- **対応設計ID**: DS-CL-ITEM-REGISTER-VIEW-UI-ITEM-REGISTER-SCREEN
- **完了条件**: 
  - 資産管理番号入力フィールドが実装されている
  - 名称入力フィールドが実装されている
  - 登録ボタンが実装されている
  - キャンセルボタンが実装されている
  - 登録ボタンクリック時に ApiClient.createItem() を呼び出す
  - 登録成功時は /items へリダイレクトする
  - 登録失敗時はエラーメッセージを表示する
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 備品登録が正しく動作すること

#### TASK-020: ItemEditView 実装
- **内容**: frontend/src/views/ItemEditView.vue に備品編集画面を実装する
- **対応設計ID**: DS-CL-ITEM-EDIT-VIEW-UI-ITEM-EDIT-SCREEN
- **完了条件**: 
  - 資産管理番号表示フィールド（編集不可）が実装されている
  - 名称入力フィールドが実装されている
  - 更新ボタンが実装されている
  - キャンセルボタンが実装されている
  - 画面表示時に ApiClient.getItem() を呼び出して備品情報を取得する
  - 更新ボタンクリック時に ApiClient.updateItem() を呼び出す
  - 更新成功時は /items へリダイレクトする
  - 更新失敗時はエラーメッセージを表示する
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 備品編集が正しく動作すること

#### TASK-021: UserListView 実装
- **内容**: frontend/src/views/UserListView.vue に利用者一覧画面を実装する
- **対応設計ID**: DS-CL-USER-LIST-VIEW-UI-USER-LIST-SCREEN
- **完了条件**: 
  - 利用者一覧テーブル（ユーザーID、氏名、権限）が実装されている
  - 画面表示時に ApiClient.getUsers() を呼び出して利用者一覧を取得する
  - 利用者登録ボタンが実装されている
  - 編集ボタンが実装されている
  - 削除ボタンが実装されている
  - 戻るボタンが実装されている
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 利用者一覧が表示され、各ボタンが正しく動作すること

#### TASK-022: UserRegisterView 実装
- **内容**: frontend/src/views/UserRegisterView.vue に利用者登録画面を実装する
- **対応設計ID**: DS-CL-USER-REGISTER-VIEW-UI-USER-REGISTER-SCREEN
- **完了条件**: 
  - ユーザーID入力フィールドが実装されている
  - 氏名入力フィールドが実装されている
  - パスワード入力フィールドが実装されている
  - 権限選択フィールド（管理者 / 一般利用者）が実装されている
  - 登録ボタンが実装されている
  - キャンセルボタンが実装されている
  - 登録ボタンクリック時に ApiClient.createUser() を呼び出す
  - 登録成功時は /users へリダイレクトする
  - 登録失敗時はエラーメッセージを表示する
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 利用者登録が正しく動作すること

#### TASK-023: UserEditView 実装
- **内容**: frontend/src/views/UserEditView.vue に利用者編集画面を実装する
- **対応設計ID**: DS-CL-USER-EDIT-VIEW-UI-USER-EDIT-SCREEN
- **完了条件**: 
  - ユーザーID表示フィールド（編集不可）が実装されている
  - 氏名入力フィールドが実装されている
  - パスワード入力フィールド（オプション）が実装されている
  - 権限選択フィールド（管理者 / 一般利用者）が実装されている
  - 更新ボタンが実装されている
  - キャンセルボタンが実装されている
  - 画面表示時に ApiClient.getUser() を呼び出して利用者情報を取得する
  - 更新ボタンクリック時に ApiClient.updateUser() を呼び出す
  - 更新成功時は /users へリダイレクトする
  - 更新失敗時はエラーメッセージを表示する
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 利用者編集が正しく動作すること

#### TASK-024: LendingView 実装
- **内容**: frontend/src/views/LendingView.vue に貸出画面を実装する
- **対応設計ID**: DS-CL-LENDING-VIEW-UI-LENDING-SCREEN
- **完了条件**: 
  - 資産管理番号入力フィールドが実装されている
  - 借り主（氏名）入力フィールドが実装されている
  - 貸出ボタンが実装されている
  - キャンセルボタンが実装されている
  - 貸出ボタンクリック時に ApiClient.lendItem() を呼び出す
  - 貸出成功時は /items へリダイレクトする
  - 貸出失敗時はエラーメッセージを表示する
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 貸出処理が正しく動作すること

#### TASK-025: ReturnView 実装
- **内容**: frontend/src/views/ReturnView.vue に返却画面を実装する
- **対応設計ID**: DS-CL-RETURN-VIEW-UI-RETURN-SCREEN
- **完了条件**: 
  - 資産管理番号入力フィールドが実装されている
  - 返却ボタンが実装されている
  - キャンセルボタンが実装されている
  - 返却ボタンクリック時に ApiClient.returnItem() を呼び出す
  - 返却成功時は /items へリダイレクトする
  - 返却失敗時はエラーメッセージを表示する
  - Vuetify 3 のコンポーネントを使用する
  - 型定義が明示されている
- **バリデーション**: 返却処理が正しく動作すること

---

### 4. テスト実装

#### TASK-026: バックエンド単体テスト実装
- **内容**: backend/tests/unit/ 配下に各サービスの単体テストを実装する
- **対応設計ID**: DS-CL-AUTH-SERVICE-FT-LOGIN, DS-CL-ITEM-SERVICE-FT-REGISTER-ITEM, DS-CL-USER-SERVICE-FT-REGISTER-USER
- **完了条件**: 
  - test_auth_service.py に AuthService の全メソッドのテストが実装されている
  - test_item_service.py に ItemService の全メソッドのテストが実装されている
  - test_user_service.py に UserService の全メソッドのテストが実装されている
  - pytestで全テストが通ること
- **バリデーション**: `docker compose run backend pytest tests/unit/` で全テストが成功すること

#### TASK-027: バックエンド統合テスト実装
- **内容**: backend/tests/integration/ 配下に API統合テストを実装する
- **対応設計ID**: DS-CL-AUTH-ROUTER-FT-LOGIN, DS-CL-ITEM-ROUTER-FT-REGISTER-ITEM, DS-CL-USER-ROUTER-FT-REGISTER-USER
- **完了条件**: 
  - test_api.py に全APIエンドポイントのテストが実装されている
  - 認証、備品CRUD、利用者CRUD、貸出・返却の全機能がテストされている
  - pytestで全テストが通ること
- **バリデーション**: `docker compose run backend pytest tests/integration/` で全テストが成功すること

#### TASK-028: E2Eテスト実装
- **内容**: e2e/ 配下に Playwright による E2E テストを実装する
- **対応設計ID**: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ITEM-LIST-SCREEN-UI-ITEM-LIST-SCREEN
- **完了条件**: 
  - test_e2e.spec.ts に14個のE2Eテストシナリオ（E2E-001 〜 E2E-014）が実装されている
  - ログイン、備品CRUD、利用者CRUD、貸出・返却の全機能がテストされている
  - Playwrightで全テストが通ること
- **バリデーション**: `docker compose run e2e npx playwright test` で全テストが成功すること

---

### 5. 動作確認とバリデーション

#### TASK-029: 全体動作確認
- **内容**: docker compose up で全サービスを起動し、全機能が正常に動作することを確認する
- **対応設計ID**: 全設計ID
- **完了条件**: 
  - `docker compose up` で backend、frontend が起動すること
  - http://localhost:5173 でフロントエンドにアクセスできること
  - http://localhost:8000/docs でバックエンドAPIドキュメントにアクセスできること
  - 初期管理者（admin/admin）でログインできること
  - 備品一覧画面が表示されること
  - 備品登録、編集、削除、貸出、返却が正しく動作すること
  - 利用者一覧画面が表示されること
  - 利用者登録、編集、削除が正しく動作すること
  - 一般利用者でログインした場合、備品一覧の閲覧のみ可能であること
  - レスポンス時間が5秒以内であること
- **バリデーション**: 全機能を手動で操作し、正常に動作することを確認する

#### TASK-030: README.md 作成
- **内容**: プロジェクトルートに README.md を作成し、起動方法と操作説明を記載する
- **対応設計ID**: DS-MD-DOCKER-COMPOSE-DT-DOCKER-COMPOSE
- **完了条件**: 
  - 前提条件（Docker、Docker Composeのインストール）が記載されている
  - 起動コマンド（docker compose up）が記載されている
  - 初期ユーザー情報（admin / admin）が記載されている
  - アクセスURL（フロントエンド: http://localhost:5173、バックエンドAPI: http://localhost:8000）が記載されている
  - 停止コマンド（docker compose down）が記載されている
  - 基本的な操作説明が記載されている
- **バリデーション**: README.mdの手順に従って起動し、動作することを確認する

#### TASK-031: 全実装完了確認
- **内容**: 全タスク（TASK-001 〜 TASK-030）が完了していることを確認する
- **対応設計ID**: 全設計ID
- **完了条件**: 
  - 全タスクが完了している
  - 全テスト（単体テスト、統合テスト、E2Eテスト）が成功している
  - 全機能が正常に動作している
  - 要件定義書（docs/requirements.md）の全要件が満たされている
  - 詳細設計書（docs/detail_design.md）の全設計が実装されている
- **バリデーション**: 
  - `docker compose run backend pytest` で全バックエンドテストが成功すること
  - `docker compose run e2e npx playwright test` で全E2Eテストが成功すること
  - 手動で全機能を操作し、正常に動作することを確認する

---

## タスク実施の注意事項

1. **実装順序**: タスクは TASK-001 から順番に実施すること
2. **完了条件の確認**: 各タスク完了時に完了条件を必ず確認すること
3. **バリデーションの実施**: 各タスク完了時にバリデーションを必ず実施すること
4. **コーディング規約**: PEP8（Python）、ESLint + Prettier（TypeScript）に準拠すること
5. **型ヒント・型定義**: 全関数・変数に型ヒント・型定義を付与すること
6. **docstring・コメント**: 全関数・クラスにdocstringまたはコメントを記述すること
7. **エラー処理**: 全APIエンドポイント、全画面で適切なエラー処理を実装すること
8. **設計IDの対応**: 実装時に対応する設計IDをコメントに記載すること

---

## 完了判定

以下の条件を全て満たした場合、本プロジェクトの実装が完了したと判定する：

- ✅ 全タスク（TASK-001 〜 TASK-031）が完了している
- ✅ 全テスト（単体テスト、統合テスト、E2Eテスト）が成功している
- ✅ `docker compose up` で全サービスが起動する
- ✅ http://localhost:5173 でフロントエンドにアクセスでき、全機能が正常に動作する
- ✅ http://localhost:8000/docs でバックエンドAPIドキュメントにアクセスできる
- ✅ 要件定義書（docs/requirements.md）の全要件（RQ-*）が満たされている
- ✅ 詳細設計書（docs/detail_design.md）の全設計（DS-*）が実装されている
- ✅ README.md の手順に従って起動・操作できる

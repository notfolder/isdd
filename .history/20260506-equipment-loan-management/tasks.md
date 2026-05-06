# 備品管理・貸出管理アプリ 実装タスク

## 1. プロジェクト基盤

| タスクID | 対応設計ID | タスク | 完了条件 | バリデーション |
|---|---|---|---|---|
| TASK-001 | DS-MD-CONTAINER-RUNTIME-NF-USERS-ADMIN-3-GENERAL-30 | docker compose、Nginx、FastAPI、Vueの基本構成を作成する。 | `web` と `api` がdocker composeで起動し、ブラウザから画面へアクセスできる。 | docker composeで通常起動し、ログイン画面が表示されることを確認する。 |
| TASK-002 | DS-MD-BACKEND-CONFIG-OP-INITIAL-ADMIN-ENV | 環境変数読み込みとアプリ設定を実装する。 | 初期管理者ログインID、初期管理者パスワード、DBパスを読み込める。 | 環境変数未設定時に起動時エラーとして検知できることを確認する。 |
| TASK-003 | DS-MD-README-OP-INITIAL-ADMIN-ENV | READMEに起動方法、初期管理者設定、操作概要、E2E実行方法を記載する。 | READMEだけで起動とログインとテスト実行の手順が分かる。 | READMEの手順どおりに起動とログイン確認を行う。 |

## 2. データベース

| タスクID | 対応設計ID | タスク | 完了条件 | バリデーション |
|---|---|---|---|---|
| TASK-004 | DS-SC-DATABASE-REQUIRED-DT-APP-DATABASE-REQUIRED | SQLite接続、DBセッション、トランザクション管理を実装する。 | API要求単位でDBトランザクションを開始し、成功時に確定、失敗時にロールバックできる。 | DBエラー時にデータが途中保存されないことを単体テストで確認する。 |
| TASK-005 | DS-SC-USERS-DT-BORROWER-FIELDS | 利用者テーブルとモデルを実装する。 | 利用者名、ログインID、パスワードハッシュ、権限種別、versionを保存できる。 | ログインID一意制約と権限種別制約を単体テストで確認する。 |
| TASK-006 | DS-SC-EQUIPMENT-DT-EQUIPMENT-FIELDS | 備品テーブルとモデルを実装する。 | 備品ID、備品名、状態、貸出先、貸出日、versionを保存できる。 | 備品ID一意制約と状態制約を単体テストで確認する。 |
| TASK-007 | DS-SC-SESSIONS-NF-SESSION-AUTO-LOGOUT-60MIN | セッションテーブルとモデルを実装する。 | セッションID、利用者ID、最終操作時刻、期限を保存できる。 | 期限切れセッションを無効扱いにできることを単体テストで確認する。 |

## 3. バックエンド機能

| タスクID | 対応設計ID | タスク | 完了条件 | バリデーション |
|---|---|---|---|---|
| TASK-008 | DS-BT-INITIAL-ADMIN-OP-INITIAL-ADMIN-ENV | 初回起動時の初期管理者作成を実装する。 | 利用者が0件の場合だけ環境変数から管理者利用者が作成される。 | 初回起動時に管理者ログインでき、2回目以降に重複作成されないことを確認する。 |
| TASK-009 | DS-CL-PASSWORD-SERVICE-NF-PASSWORD-HASH-STORAGE | パスワードハッシュ化と照合を実装する。 | 平文パスワードを保存せず、bcryptハッシュで照合できる。 | DBに平文パスワードが保存されないことを単体テストで確認する。 |
| TASK-010 | DS-CL-AUTH-SERVICE-FT-LOGIN | ログイン、ログアウト、ログイン利用者取得を実装する。 | 管理者と一般利用者がログインでき、ログアウトでセッションが削除される。 | 正常ログイン、不正ログイン、ログアウト後アクセス不可をAPIテストで確認する。 |
| TASK-011 | DS-FN-AUTO-LOGOUT-NF-SESSION-AUTO-LOGOUT-60MIN | 未操作60分の自動ログアウトを実装する。 | 最終操作から60分超過したセッションは無効化される。 | 時刻を制御した単体テストで60分以内は有効、60分超過は無効になることを確認する。 |
| TASK-012 | DS-CL-AUTHORIZATION-SERVICE-NF-ROLE-BASED-AUTHORIZATION | 管理者権限と一般利用者権限の認可を実装する。 | 管理者だけが更新APIを利用でき、一般利用者は閲覧APIだけ利用できる。 | 一般利用者で管理者APIが拒否されることをAPIテストで確認する。 |
| TASK-013 | DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT | 備品登録、編集、削除、一覧取得を実装する。 | 備品を登録・編集でき、貸出可能な備品だけ削除できる。 | 貸出中備品削除不可、重複備品ID不可、version競合を単体・APIテストで確認する。 |
| TASK-014 | DS-CL-USER-SERVICE-FT-MANAGE-BORROWER | 利用者登録、編集、削除、一覧取得を実装する。 | 利用者を登録・編集・削除でき、削除不可条件と最後の管理者保護が効く。 | 貸出中利用者削除不可、自分自身削除不可、最後の管理者削除不可、最後の管理者の一般利用者変更不可を確認する。 |
| TASK-015 | DS-CL-LOAN-SERVICE-FT-LOAN-EQUIPMENT | 貸出処理を実装する。 | 貸出可能備品に貸出先利用者と貸出日を設定し、状態を貸出中にできる。 | 貸出中備品の再貸出不可、存在しない利用者への貸出不可、version競合を確認する。 |
| TASK-016 | DS-CL-LOAN-SERVICE-FT-LOAN-EQUIPMENT | 返却処理を実装する。 | 貸出中備品を貸出可能に戻し、貸出先利用者と貸出日を空にできる。 | 貸出可能備品の返却不可、返却後に貸出先と貸出日が表示されないことを確認する。 |
| TASK-017 | DS-CL-API-ERROR-HANDLER-FT-VIEW-EQUIPMENT-LIST | APIエラー応答を統一する。 | 認証失敗、権限不足、入力不備、業務制約違反、競合が画面で扱える形式で返る。 | 各エラーケースのAPIテストでエラー種別とメッセージを確認する。 |

## 4. フロントエンド画面

| タスクID | 対応設計ID | タスク | 完了条件 | バリデーション |
|---|---|---|---|---|
| TASK-018 | DS-MD-FRONTEND-API-FT-VIEW-EQUIPMENT-LIST | APIクライアントと認証状態管理を実装する。 | API呼び出し、ログイン状態、権限種別、未ログイン時遷移を共通化できる。 | ログイン前後のルート制御をフロントエンドテストで確認する。 |
| TASK-019 | DS-MD-LOGIN-SCREEN-UI-LOGIN-SCREEN | ログイン画面を実装する。 | ログインIDとパスワードを入力し、権限別の画面へ遷移できる。 | 管理者と一般利用者の遷移先が異なることを画面テストで確認する。 |
| TASK-020 | DS-MD-ADMIN-EQUIPMENT-LIST-UI-ADMIN-EQUIPMENT-LIST-SCREEN | 管理者向け備品一覧画面を実装する。 | 備品ID、備品名、状態、貸出先利用者名、貸出日、各操作への遷移を表示できる。 | 貸出可能と貸出中で表示される操作が正しいことを画面テストで確認する。 |
| TASK-021 | DS-MD-EQUIPMENT-FORM-UI-EQUIPMENT-FORM-SCREEN | 備品登録・編集画面を実装する。 | 備品IDと備品名を登録・編集でき、完了後に一覧へ戻る。 | 必須入力エラーと正常登録・編集を画面テストで確認する。 |
| TASK-022 | DS-MD-EQUIPMENT-DELETE-UI-EQUIPMENT-DELETE-CONFIRM-SCREEN | 備品削除確認画面を実装する。 | 削除対象を確認し、貸出可能備品だけ削除できる。 | 貸出中備品の削除操作ができないことを画面テストで確認する。 |
| TASK-023 | DS-MD-LOAN-FORM-UI-LOAN-FORM-SCREEN | 貸出登録画面を実装する。 | 貸出可能備品、貸出先利用者、貸出日を入力して貸出できる。 | 貸出後に一覧で貸出中、貸出先、貸出日が表示されることを確認する。 |
| TASK-024 | DS-MD-RETURN-CONFIRM-UI-RETURN-CONFIRM-SCREEN | 返却確認画面を実装する。 | 貸出中備品を確認して返却できる。 | 返却後に貸出可能となり、貸出先と貸出日が非表示になることを確認する。 |
| TASK-025 | DS-MD-BORROWER-LIST-UI-BORROWER-LIST-SCREEN | 利用者一覧画面を実装する。 | 利用者名、ログインID、権限種別を表示し、パスワードを表示しない。 | パスワードまたはパスワードハッシュが画面に出ないことを確認する。 |
| TASK-026 | DS-MD-BORROWER-FORM-UI-BORROWER-FORM-SCREEN | 利用者登録・編集画面を実装する。 | 利用者名、ログインID、パスワード、権限種別を登録・編集できる。 | 最後の管理者の権限変更不可と正常編集を画面テストで確認する。 |
| TASK-027 | DS-MD-BORROWER-DELETE-UI-BORROWER-DELETE-CONFIRM-SCREEN | 利用者削除確認画面を実装する。 | 削除対象を確認し、削除可能な利用者だけ削除できる。 | 貸出中利用者、自分自身、最後の管理者を削除できないことを確認する。 |
| TASK-028 | DS-MD-GENERAL-EQUIPMENT-LIST-UI-GENERAL-EQUIPMENT-LIST-SCREEN | 一般利用者向け備品一覧画面を実装する。 | 全備品の備品ID、備品名、状態を閲覧専用で表示できる。 | 登録・編集・削除・貸出・返却操作が表示されないことを確認する。 |

## 5. テストと品質確認

| タスクID | 対応設計ID | タスク | 完了条件 | バリデーション |
|---|---|---|---|---|
| TASK-029 | DS-MD-BACKEND-UNIT-TESTS-FT-MANAGE-EQUIPMENT | バックエンド単体テストを実装する。 | AuthService、AuthorizationService、EquipmentService、UserService、LoanService、PasswordServiceの正常系・異常系を網羅する。 | バックエンド単体テストが全件成功する。 |
| TASK-030 | DS-MD-BACKEND-INTEGRATION-TESTS-FT-LOAN-EQUIPMENT | API結合テストを実装する。 | 認証、認可、備品、利用者、貸出、返却APIをDB込みで検証できる。 | API結合テストが全件成功する。 |
| TASK-031 | DS-MD-FRONTEND-UNIT-TESTS-UI-WEB-GUI | フロントエンド単体テストを実装する。 | 主要画面、ルート制御、権限別表示、エラー表示を検証できる。 | フロントエンド単体テストが全件成功する。 |
| TASK-032 | DS-MD-PLAYWRIGHT-SERVICE-TS-VERIFY-GENERAL-EQUIPMENT-VIEW | Playwright E2E環境を実装する。 | `test_playwright` サービスが `test` プロファイルで起動し、`e2e` 配下のテストを実行できる。 | 設計書記載のE2E実行コマンドでテストが起動する。 |
| TASK-033 | DS-MD-E2E-ADMIN-LOGIN-TS-VERIFY-ADMIN-LOGIN | E2Eシナリオを実装する。 | 要件定義書の全テスト用利用シナリオをE2Eで網羅する。 | 管理者ログイン、一般利用者ログイン、初期管理者作成、備品管理、利用者管理、貸出、返却、一般利用者閲覧、ログアウト、自動ログアウトが全件成功する。 |
| TASK-034 | DS-MD-TRACEABLE-COMMENT-RULES-BZ-EQUIPMENT-LOAN-MANAGEMENT | トレーサブルコメントを適用する。 | 主要な関数、クラス、モジュールに対応RQ-IDとDS-IDが記載される。 | 実装後に対象ファイルを確認し、IDなしの主要要素がないことを確認する。 |
| TASK-035 | DS-MD-REMOVE-LOAN-HISTORY-DT-LOAN-STATE-FIELDS | MVP外設計が実装されていないことを確認する。 | 貸出履歴、返却予定日、返却日、検索、業務操作ログ、監視・アラート、独立したログイン情報管理が実装されていない。 | コードと画面を確認し、MVP外要素がないことを確認する。 |
| TASK-036 | DS-MD-E2E-TESTS-TS-VERIFY-GENERAL-EQUIPMENT-VIEW | 全体確認を実施する。 | 要件定義書と詳細設計書の全要件・全設計要素に対応する実装とテストが完了している。 | 単体テスト、API結合テスト、フロントエンドテスト、E2Eテストを全件成功させ、画面上の主要操作を確認する。 |

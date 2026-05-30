# 実装タスク一覧

## タスク1: 認証基盤実装
- 対象: ログイン認証、権限制御、セッション管理の最小実装
- 対応設計ID: DS-CL-AUTH-SERVICE-FT-AUTHENTICATE-USER, DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-FN-ROLE-AUTHORIZATION-NF-LOW-SECURITY-POLICY, DS-FN-PASSWORD-HASH-NF-LOW-SECURITY-POLICY, DS-FN-SESSION-POLICY-NF-LOW-SECURITY-POLICY
- 完了条件:
  - 管理担当者と一般利用者がログインできる
  - 権限に応じて更新操作の表示/非表示が切り替わる
  - パスワードが平文で保存されない
- バリデーション:
  - AuthService の単体テストが通る
  - 権限制御の E2E シナリオが通る

## タスク2: SQLite スキーマと初期化処理実装
- 対象: users、assets、loan_status テーブル、初期管理ユーザー投入
- 対応設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY, DS-SC-USERS-DT-USER-ACCOUNT-ENTITY, DS-SC-ASSETS-DT-ASSET-ENTITY, DS-SC-LOAN-STATUS-DT-LOAN-STATUS-ENTITY, DS-SC-DATA-BOUNDARY-DT-INTERNAL-EXTERNAL-DATA-BOUNDARY, DS-SC-RETENTION-POLICY-DT-DATA-RETENTION-POLICY, DS-IF-NO-EXTERNAL-DB-DT-EXTERNAL-DB-CONNECTION-NONE
- 完了条件:
  - DB 作成時に全テーブルと制約が生成される
  - 初期管理ユーザーが自動投入される
  - 返却済み履歴を保持しないデータ更新方式が実装される
- バリデーション:
  - スキーマ適用テストが通る
  - 初期化後にテーブル構造と初期データを確認できる

## タスク3: 備品マスタ管理実装
- 対象: 備品登録、更新、一覧検索、状態表示
- 対応設計ID: DS-CL-ASSET-SERVICE-FT-MANAGE-ASSET-MASTER, DS-FN-MANAGE-ASSET-MASTER-FT-MANAGE-ASSET-MASTER, DS-FN-VIEW-ASSET-STATUS-FT-VIEW-ASSET-STATUS, DS-IF-ASSET-LIST-SCREEN-UI-ASSET-LIST-SCREEN, DS-CL-ASSET-REPOSITORY-DT-ASSET-ENTITY
- 完了条件:
  - 備品の新規登録と更新ができる
  - 備品一覧で状態と貸出中利用者名が表示される
  - 検索条件で一覧絞り込みができる
- バリデーション:
  - AssetService の単体テストが通る
  - 備品一覧の結合テストが通る

## タスク4: 貸出入力ポップアップと貸出登録実装
- 対象: 貸出ボタン押下時のポップアップ表示、必須入力チェック、貸出確定
- 対応設計ID: DS-IF-LOAN-POPUP-SCREEN-UI-LOAN-ENTRY-POPUP, DS-IF-LOAN-POPUP-SUBMIT-UI-LOAN-ENTRY-POPUP, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-LOAN-TX-BOUNDARY-FT-REGISTER-LOAN, DS-FN-ASSET-OPTIMISTIC-LOCK-FT-REGISTER-LOAN, DS-EV-LOAN-REGISTERED-FT-REGISTER-LOAN, DS-FN-ERR-LOAN-REQUIRED-UI-LOAN-ENTRY-POPUP, DS-FN-ERR-STATE-CONFLICT-FT-REGISTER-LOAN
- 完了条件:
  - 貸出ボタン押下でポップアップが表示される
  - 貸出先と返却予定日が未入力の場合にエラー表示される
  - 入力後に貸出状態が loaned へ更新される
  - 同時更新競合時に再読込エラーが表示される
- バリデーション:
  - LoanService の単体テストが通る
  - 貸出フローの E2E テストが通る

## タスク5: 返却登録実装
- 対象: 返却ボタン、返却日入力、返却確定、状態復帰
- 対応設計ID: DS-FN-REGISTER-RETURN-FT-REGISTER-RETURN, DS-FN-RETURN-TX-BOUNDARY-FT-REGISTER-RETURN, DS-FN-ASSET-OPTIMISTIC-LOCK-FT-REGISTER-RETURN, DS-IF-RETURN-SUBMIT-FT-REGISTER-RETURN, DS-EV-RETURN-REGISTERED-FT-REGISTER-RETURN, DS-FN-ERR-RETURN-INVALID-FT-REGISTER-RETURN
- 完了条件:
  - 貸出中備品のみ返却操作できる
  - 返却登録後に状態が available へ戻る
  - 不正状態の返却時にエラー表示される
- バリデーション:
  - 返却処理の結合テストが通る
  - 返却フローの E2E テストが通る

## タスク6: ユーザー管理画面実装
- 対象: ユーザー登録、更新、有効/無効切替
- 対応設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-CL-USER-SERVICE-FT-MANAGE-USER-ACCOUNT, DS-FN-MANAGE-USER-ACCOUNT-FT-MANAGE-USER-ACCOUNT, DS-CL-USER-REPOSITORY-DT-USER-ACCOUNT-ENTITY
- 完了条件:
  - 氏名、ログインID、パスワード、権限、有効/無効を管理できる
  - 重複ログインIDを拒否できる
  - 無効ユーザーはログインできない
- バリデーション:
  - UserService の単体テストが通る
  - ユーザー管理画面の結合テストが通る

## タスク7: Docker Compose 起動・初期化構成実装
- 対象: アプリ起動、DB初期化、自動セットアップ
- 対応設計ID: DS-SC-SQLITE-SCHEMA-DT-DB-NECESSITY
- 完了条件:
  - docker compose up でアプリが起動する
  - 起動時に DB 初期化が自動実行される
  - 初期管理ユーザーでログイン可能である
- バリデーション:
  - コンテナ起動確認
  - 初回起動からログインまでの手順確認

## タスク8: E2E 実行基盤実装
- 対象: Playwright サービス、e2e ディレクトリ、実行コマンド整備
- 対応設計ID: DS-IF-E2E-LOGIN-TS-VERIFY-LOGIN-ROLE-CONTROL, DS-IF-E2E-LOAN-TS-VERIFY-LOAN-FLOW, DS-IF-E2E-RETURN-TS-VERIFY-RETURN-FLOW, DS-IF-E2E-VISIBILITY-TS-VERIFY-STATUS-VISIBILITY
- 完了条件:
  - test_playwright サービスが test プロファイルで起動できる
  - E2E テスト資産が e2e 配下に配置される
  - 設計書記載のコマンドで E2E を実行できる
- バリデーション:
  - Playwright 実行環境起動確認
  - 4本の E2E シナリオが全て実行できる

## タスク9: README 更新
- 対象: 起動方法、操作方法、テスト実行方法の記載
- 対応設計ID: DS-MD-STREAMLIT-UI-UI-ASSET-LIST-SCREEN
- 完了条件:
  - 起動手順が README に記載されている
  - 管理担当者と一般利用者の操作方法が記載されている
  - 単体/結合/E2E テストの実行方法が記載されている
- バリデーション:
  - README の記載だけで起動とテスト実行が再現できる

## タスク10: 全体確認
- 対象: 全変更点の実装完了確認
- 完了条件:
  - docs/requirements.md と docs/detail_design.md に対応する実装が全て存在する
  - 単体、結合、E2E の全テストが成功する
  - 管理担当者/一般利用者の主要操作が手順どおり再現できる
- バリデーション:
  - 実装済み機能と RQ/DS 対応表を照合する
  - テスト結果と画面確認結果を記録する

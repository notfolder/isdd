# 備品台帳・貸出状況システム 実装タスク

詳細設計書: `docs/detail_design.md`。要件定義書: `docs/requirements.md`。実装はこのファイルを上から順に行う。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が存在しなければ `isdd-setup` を実行して対応表チェックを導入する。導入時は詳細設計書の実行形態（サーバー）、認証の有無（有り）、外部連携の有無（無し）、対応表の粒度（function）を渡し、第 7 章の依存の規則を `scripts/isdd/dependencies.json` に書き写す。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること。

## 1. 共通基盤（DB・設定・入力検査・パスワード・セッション）

- 1-1. 設定の読み込み（DS-MD-CONFIG、DS-FN-LOAD-SETTINGS）。環境変数 PORT、DATA_DIR、SESSION_IDLE_TIMEOUT_SECONDS を読む。
- 1-2. DB 接続とスキーマ（DS-MD-DATABASE、DS-FN-OPEN-CONNECTION、DS-FN-INITIALIZE-SCHEMA、DS-SC-DATABASE-FILE、DS-SC-ACCOUNTS、DS-SC-EQUIPMENT、DS-SC-LENDING、DS-SC-SESSIONS）。WAL、外部キー、busy タイムアウト、BEGIN IMMEDIATE のヘルパー。
- 1-3. パスワード（DS-MD-SECURITY、DS-FN-HASH-PASSWORD、DS-FN-VERIFY-PASSWORD、DS-FN-NEW-SESSION-TOKEN）。
- 1-4. 入力検査（DS-MD-VALIDATION、DS-FN-VALIDATE-EMPLOYEE-NUMBER、DS-FN-VALIDATE-NAME、DS-FN-VALIDATE-PASSWORD、DS-FN-VALIDATE-EQUIPMENT-NUMBER、DS-FN-VALIDATE-EQUIPMENT-NAME、DS-FN-VALIDATE-LENT-ON）。
- 完了条件: 単体テスト（tests/unit）で各検査の境界値（5 桁・6 桁・7 桁、30 文字・31 文字、7 文字・8 文字、20 文字・21 文字、50 文字・51 文字、今日・明日）が通ること。

## 2. セッションとアカウント

- 2-1. セッション（DS-MD-SESSIONS、DS-FN-CREATE-SESSION、DS-FN-RESOLVE-SESSION、DS-FN-DELETE-SESSION、DS-FN-REQUIRE-MANAGER）。最終操作からの秒数で期限切れにする。
- 2-2. アカウント（DS-MD-ACCOUNTS、DS-FN-REGISTER-ACCOUNT、DS-FN-AUTHENTICATE-ACCOUNT、DS-FN-LIST-ACCOUNTS、DS-FN-CHANGE-MANAGER-ROLE、DS-FN-RESET-PASSWORD、DS-FN-DELETE-ACCOUNT）。登録は BEGIN IMMEDIATE 内で件数を数え、最初の 1 件を担当者にする。50 件の上限、担当者 0 人の禁止、借りている社員の削除の禁止を含む。
- 完了条件: 結合テストで、同時登録の 2 件目以降が社員になること、担当者が 0 人にならないこと、借りている社員を削除できないことを確かめる。

## 3. 備品と貸出

- 3-1. 備品（DS-MD-EQUIPMENT、DS-FN-CREATE-EQUIPMENT、DS-FN-UPDATE-EQUIPMENT、DS-FN-DELETE-EQUIPMENT、DS-FN-CHECK-EQUIPMENT-VERSION）。版番号の検査、管理番号の重複、貸出中の削除の禁止。
- 3-2. 貸出（DS-MD-LENDING、DS-FN-LIST-LENDING-STATUS、DS-FN-LEND-EQUIPMENT、DS-FN-RETURN-EQUIPMENT）。貸出の登録と返却はトランザクションで行い、返却で貸出行を削除する。
- 完了条件: 結合テストで、貸出中への貸出が拒否されること、空きへの返却が拒否されること、版番号の不一致が拒否されることを確かめる。

## 4. 画面（HTTP）

- 4-1. 起動の入口（DS-MD-MAIN、DS-FN-MAIN、DS-OP-SERVER-START、DS-MD-RUN-SCRIPT、DS-MD-SETUP-SCRIPT、DS-MD-CONFIG の起動部分）。`PORT` で待ち受け、全インターフェースに bind する。`run.sh` は環境変数の既定値を補い、`python3 -m app` を起動する。`setup.sh` は Python 3.12 以上と sqlite3 を確かめる。
- 4-2. 画面の部品（DS-MD-TEMPLATES、DS-FN-RENDER-PAGE）。`.current-user`、`.message`、`.error`、`.field`、`.field-error` を共通の枠で出す。値は HTML エスケープする。
- 4-3. 画面の処理（DS-MD-WEB、DS-CL-REQUEST-HANDLER、DS-IF-LENDING-STATUS-SCREEN、DS-IF-REGISTER-ACCOUNT-SCREEN、DS-IF-LOGIN-SCREEN、DS-IF-EQUIPMENT-FORM-SCREEN、DS-IF-LENDING-FORM-SCREEN、DS-IF-ACCOUNT-LIST-SCREEN）。契約の URL、要素の id、ボタンの文言、リンクの文言、data 属性、文言を守る。Cookie（sid）と flash の Cookie を扱う。担当者の操作は業務ロジックを呼ぶ前に検査する。
- 4-4. 運用の手順（DS-OP-INITIAL-SETUP）。README.md に起動方法、環境変数、最初の担当者の登録の手順を書く。
- 完了条件: `bash setup.sh` のあとで `PORT=8795 DATA_DIR=/tmp/isdd-r2-data bash run.sh` が起動し、契約の URL が開けること。

## 5. テスト

- 5-1. 単体テストと結合テスト（tests/unit）。`python3 -m unittest discover -s tests/unit` で全件通過。
- 5-2. E2E テスト（e2e）。DS-TS-REGISTER-ACCOUNTS、DS-TS-LOGIN-LOGOUT、DS-TS-IDLE-LOGOUT、DS-TS-VIEW-LENDING-STATUS、DS-TS-EMPTY-EQUIPMENT-LIST、DS-TS-CREATE-EQUIPMENT、DS-TS-UPDATE-EQUIPMENT、DS-TS-DELETE-EQUIPMENT、DS-TS-LEND-EQUIPMENT、DS-TS-RETURN-EQUIPMENT、DS-TS-MANAGE-MANAGER-ROLE、DS-TS-RESET-PASSWORD、DS-TS-DELETE-ACCOUNT、DS-TS-RESTRICT-NON-MANAGER の 14 件を、それぞれテスト関数に結ぶ。
- 5-3. 非機能のテスト（DS-TS-RESPONSE-TIME、DS-TS-CONCURRENT-USERS）。
- 完了条件: E2E は 8-4 のコマンドで全件通過し、`e2e/results/e2e.xml` が出ること。

## 6. 実装完了の確認（固定タスク）

1. **対応表（docs/trace_map.md）更新タスク**: 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する。完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。
2. **起動確認タスク**: 詳細設計書第 9 章の `bash setup.sh` と `bash run.sh` で起動できること。完了条件: 起動がエラーなく完了し、契約の URL が開けること。
3. **単体テスト・結合テスト全件通過タスク**: `python3 -m unittest discover -s tests/unit`。完了条件: FAIL が 0 件。
4. **E2E テスト全件通過タスク**: 8-4 のコマンドで e2e を全件実行し、JUnit XML を `e2e/results/` に出す。完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返す。
5. **README.md 記載タスク**: 起動方法と初期ユーザーの手順（最初の担当者の登録）を書く。完了条件: README を読むだけで初回起動と初期登録が完結すること。
6. **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。完了条件: 全項目が OK であること。

### 条件付きタスクの扱い

- 変更フローの 0-2（進行中の変更の登録確認）: 新規フローのため対象外（新規フローには docs/active_change が無い）。
- 外部連携の接続確認・連携ライブラリ・モック: 対象外（外部連携は無い）。

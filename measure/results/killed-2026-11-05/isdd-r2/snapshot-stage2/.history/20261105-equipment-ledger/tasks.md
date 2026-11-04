# 実装タスク（備品の台帳と貸出状況の閲覧）

入力: `docs/requirements.md`、`docs/detail_design.md`。上から順に進める。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。導入時の値: 実行形態 `server`、認証あり、外部連携なし、対応表の粒度 `function`、ソース `src`、E2E ディレクトリ `e2e`。
- 依存の規則は無いので `scripts/isdd/dependencies.json` は `"rules": []` のままにする。
- 完了条件: `bash scripts/isdd/check.sh` が実行できる。`scripts/isdd/completeness.json` の実行形態（server）・認証（あり）・外部連携（なし）が詳細設計書と一致している。

## 1. 基盤

1. `requirements.txt`（Flask 3.1.3、waitress 3.0.2）と `requirements-dev.txt`（Playwright 1.64.1）を作る。
   - 完了条件: `bash setup.sh` が `.venv` を作り、両方を導入して Chromium を取得する。
2. `setup.sh` と `run.sh` を作る（詳細設計書 9-1）。
   - 完了条件: `bash run.sh` が `.venv` の無い状態で案内を出して止まる。setup 後は `PORT` で待ち受ける。
3. `src/config.py`（`DS-FN-LOAD-SETTINGS`）: `PORT`・`DATA_DIR`・`SESSION_IDLE_TIMEOUT_SECONDS` を読む。
   - 完了条件: 単体テストで既定値（8000、`./data`、1800）と環境変数の上書きを確かめる。
4. `src/db.py`（`DS-FN-CONNECT`、`DS-FN-INIT-SCHEMA`）: 接続（外部キーを有効化、`timeout=5`）、3 テーブルの作成（`DS-SC-ACCOUNT-TABLE`、`DS-SC-EQUIPMENT-TABLE`、`DS-SC-SESSION-TABLE`）。
   - 完了条件: 一時 DB でスキーマが作られ、再実行しても壊れない。

## 2. 入力検査とアカウント

5. `src/validation.py`（`DS-FN-VALIDATE-ACCOUNT-INPUT`、`DS-FN-VALIDATE-EQUIPMENT-INPUT`）: 契約の文言どおりのエラーを項目ごとに集める。
   - 完了条件: 単体テストで、社員番号の形式、名前の空と 30 文字超、パスワードの 8 文字未満、管理番号の形式と 20 文字超、備品名の 50 文字超が契約の文言で返る。
6. `src/accounts.py`（`DS-FN-HASH-PASSWORD`、`DS-FN-REGISTER-ACCOUNT`、`DS-FN-VERIFY-LOGIN`）: PBKDF2 のハッシュ、登録（`BEGIN IMMEDIATE` の中で件数確認と挿入。0 件なら担当者、それ以外は社員）、照合（失敗理由を区別しない）。
   - 完了条件: 単体テストで、最初の登録が担当者、2 件目が社員、社員番号の重複が拒否されること、誤りの照合が False になること。

## 3. セッションと権限

7. `src/sessions.py`（`DS-FN-CREATE-SESSION`、`DS-FN-RESOLVE-SESSION`、`DS-FN-DELETE-SESSION`）: 無作為トークン、無操作の期限判定、削除。
   - 完了条件: 単体テストで期限切れが未ログイン扱いになり、有効なら最終操作時刻が更新されること。
8. `src/auth.py`（`DS-FN-CURRENT-USER`、`DS-FN-REQUIRE-MANAGER`）: 現在の利用者の取得、担当者の判定（未ログインはログイン画面へ、社員は「この操作は担当者だけが行えます」）。
   - 完了条件: 単体テストで 3 種の利用者の判定が正しいこと。
9. `src/equipment.py`（`DS-FN-LIST-EQUIPMENT`、`DS-FN-GET-EQUIPMENT`、`DS-FN-CREATE-EQUIPMENT`、`DS-FN-UPDATE-EQUIPMENT`、`DS-FN-DELETE-EQUIPMENT`）: 一覧（管理番号の昇順）、取得、登録・修正（`BEGIN IMMEDIATE`、重複は契約の文言）、削除（存在しなければ「備品が見つかりません」）。
   - 完了条件: 単体テストで並び順、重複、修正の自己重複の除外、削除の結果を確かめる。

## 4. 画面

10. `src/web.py`（`DS-FN-CREATE-APP`、`DS-IF-EQUIPMENT-STATUS-SCREEN`、`DS-IF-ACCOUNT-REGISTER-SCREEN`、`DS-IF-LOGIN-SCREEN`、`DS-IF-LOGOUT-ACTION`、`DS-IF-EQUIPMENT-FORM-SCREEN`、`DS-IF-EQUIPMENT-DELETE-ACTION`）とテンプレート（`src/templates/`）、CSS（`src/static/`）。契約の id・文言・クラス（`.field`、`.field-error`、`.error`、`.message`、`.current-user`）と `tbody tr` の `data-equipment-number` を守る。
   - 完了条件: 結合テスト（Flask のテストクライアント）で、各画面の GET が 200 を返し、契約の id があること。
11. `src/main.py`（`DS-FN-MAIN`）: 設定を読み、`DATA_DIR` を作り、waitress で `0.0.0.0:PORT` を待ち受ける。
    - 完了条件: `bash run.sh` で起動し、`/` が 200 を返す。

## 5. テスト

12. `tests/`（単体・結合テスト）を作る（詳細設計書 8-1。`tests/` はトレース対象外）。
    - 完了条件: `.venv/bin/python -m unittest discover -s tests -t .` が全件通過する。
13. `e2e/`（E2E）を作る（詳細設計書 8-2）。テスト関数は `DS-TS-*-E2E` ごとに 1 つ以上。テスト関数の名前を `docs/trace_map.md` の `DS-TS` 行と一致させる。
    - 完了条件: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` が全件通過する。
14. 非機能要件のテスト（`DS-TS-NONFUNCTIONAL-LOAD-E2E`）: 備品 300 件、アカウント 50 件で `/` の表示が 3 秒以内。
    - 完了条件: 上の E2E の実行で通過する。

## 6. 文書と対応表

15. `README.md` に「起動方法」（`bash setup.sh`、`bash run.sh`、環境変数）と「初期ユーザー」（最初のアカウントは担当者が登録する。導入の順序を含む。`DS-OP-FIRST-ACCOUNT-SETUP`）を書く。
    - 完了条件: README だけで初回起動と初期登録が完結する。
16. `scripts/isdd/` の設定（isdd-setup 済み）を確認し、`.gitignore` に `e2e/results/` が入っていることを確かめる。
    - 完了条件: `.gitignore` に `e2e/results/` がある。
17. `docs/trace_map.md` を作る（粒度 `function`。書式は trace-map-rules.md）。`src/` の全ファイル、全関数、E2E テストは `DS-TS` 行で載せる。
    - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 7. 起動確認と最終確認（固定）

18. **起動確認タスク**: 実行形態 `server` のため、詳細設計書 9-1 のとおり `bash setup.sh`、`bash run.sh` で起動し、ブラウザで `/` が開くことを確かめる。
    - 完了条件: エラーなく起動する。
19. **単体・結合テスト全件通過タスク**: 上の 12 の実行コマンドで FAIL 0 件。
20. **E2E テスト全件通過タスク**: 上の 13 の実行コマンドで FAIL 0 件。失敗したら修正と再実行を繰り返す。
21. **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK。
22. **要件・設計との対応の最終確認**: `python3 .claude/skills/isdd-spec/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が合格。`bash scripts/isdd/check.sh --strict` が合格。

## 注記

- 変更フローではないため `docs/active_change` は作らない。
- 依存の規則は無いため `scripts/isdd/dependencies.json` は空のまま。

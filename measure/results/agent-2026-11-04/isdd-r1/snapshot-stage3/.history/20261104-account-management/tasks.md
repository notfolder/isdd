# タスク一覧: アカウントの管理（段 3・変更フロー）

入力: `.history/20261104-account-management/change_detail_design.md`（[追加] と [変更] の設計 ID）と `change_requirements.md`。
正本（`docs/requirements.md`・`docs/detail_design.md`）は実装の中で書き換えない。反映は実装後レビューが行う。
各タスクの完了条件を満たしてから次へ進む。テスト実行コマンドは既存の README の「テスト」の節（`.venv/bin/python -m unittest discover -s tests/unit`、`python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`）を使う。
段 1・2 の機能（アカウント登録、ログイン、備品の登録・修正・削除、貸出と返却、一覧）を壊さないこと。契約は `contract.md`（段 3 の追加分を含む）。

## 0. 導入確認（固定）

0-1. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が存在し、`scripts/isdd/VERSION` が isdd-build の版と一致していること。`scripts/isdd/dependencies.json` は段 1・2 のままでよい（変更設計書 7 章）
   - 完了条件: `bash scripts/isdd/check.sh` が実行できること

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-account-management/` を指していること
   - 完了条件: `rq_ds_link_checker.py .history/20261104-account-management/change_requirements.md .history/20261104-account-management/change_detail_design.md --base docs/requirements.md` が合格すること

## 1. 実装（設計 ID ごと）

1. **パスワードの検査**
   - 実装する設計 ID: `DS-FN-VALIDATE-PASSWORD`（`DS-MD-VALIDATION` の中の新しい関数）
   - 内容: 8 文字以上でなければ「パスワードは 8 文字以上で入力してください」を `password` に返す。空なら合格（空文字は 8 文字未満として扱う）
   - 完了条件: 単体テストで、7 文字と 8 文字の境界が確かめられること

2. **アカウントの業務（一覧・取得・役割・パスワード・削除）**
   - 実装する設計 ID: `DS-MD-ACCOUNTS`（既存のモジュール）、`DS-FN-LIST-ACCOUNTS`、`DS-FN-GET-ACCOUNT`、`DS-FN-CHANGE-ACCOUNT-ROLE`、`DS-FN-RESET-ACCOUNT-PASSWORD`、`DS-FN-DELETE-ACCOUNT`
   - 内容: 一覧は社員番号の昇順、役割を含む。`find_account_by_id` は利用者の引き直しに使う（無ければ None）。役割の変更は BEGIN IMMEDIATE で行い、対象が無ければ `ACCOUNT_NOT_FOUND`、担当者を外す操作で担当者が 1 人だけなら `ACCOUNT_LAST_MANAGER`、それ以外は `ACCOUNT_OK`。パスワードの再設定は対象が無ければ `ACCOUNT_NOT_FOUND`、そうでなければ新しいハッシュで更新して `ACCOUNT_OK`。削除は BEGIN IMMEDIATE で、対象が無ければ `ACCOUNT_NOT_FOUND`、貸出の記録（`loans.account_id`）があれば `ACCOUNT_BORROWING`、対象が担当者で担当者が 1 人だけなら `ACCOUNT_LAST_MANAGER`、それ以外は行を削除して `ACCOUNT_OK`。`app/accounts.py` は flask・views・auth を読まない
   - 完了条件: 単体テストで、一覧の順序と役割、役割の変更（2 人のとき外せる、1 人のとき外せない）、パスワード再設定後に旧パスワードで照合できないこと、削除（借りている社員は不可、担当者 1 人は不可、通常は可能で照合・一覧から消えること）

3. **利用者の引き直し（認証）**
   - 実装する設計 ID: `DS-FN-LOAD-CURRENT-USER`（変更）、`DS-MD-AUTH`、`DS-MD-APP-FACTORY`（`app/__init__.py` で `before_request` の登録を外す）
   - 内容: `load_current_user(conn)` は、セッションの利用者の id で `find_account_by_id` を引く。無ければセッションを消し `g.account = None`。あれば制限時間の判定（既存どおり）のあと、`g.account` に DB の id・名前・役割を入れる。役割はセッションの値を使わない。`app/views.py` の blueprint に `before_app_request` を置き、`_db()` の接続で呼ぶ
   - 完了条件: 段 1 の認証の単体テスト・E2E（ログイン、ログアウト、制限時間）が通ること。単体テストで、削除された利用者が未ログインになり、役割の変更が次の要求から効くこと

4. **画面（views と templates）**
   - 実装する設計 ID: `DS-MD-VIEWS`（既存のモジュール）、`DS-FN-SHOW-ACCOUNT-LIST`（`views.account_list`）、`DS-FN-SUBMIT-ACCOUNT-ROLE`（`views.account_role`）、`DS-FN-SHOW-PASSWORD-RESET` と `DS-FN-SUBMIT-PASSWORD-RESET`（`views.account_password`、GET と POST）、`DS-FN-SUBMIT-ACCOUNT-DELETE`（`views.account_delete`）、`DS-IF-ACCOUNT-LIST-SCREEN`、`DS-IF-LOAN-STATUS-SCREEN`（担当者向けの「アカウントの一覧」リンクを足す）
   - 内容: `require_manager()` を先に呼ぶ（未ログインはログイン画面、社員は貸出状況へ戻し `.message`）。役割・削除・再設定の結果は変更設計書 4-1 の文言で `.message` に出す。パスワード再設定の短い入力は、その行の `.field-error` に出す。新規テンプレート `app/templates/account_list.html`（行の `data-employee-number`、3 列目の「担当者」か「社員」、ボタン、再設定を開いた行の `input[name=new_password]` と「確定」）
   - 完了条件: 手動の確認（テストクライアント）で、契約の要素の id・文言・`data-employee-number` が出ること。E2E の追加場面（タスク 6）で確かめる

5. **トレース対応表の更新**
   - 実装する設計 ID: 上の全ての設計 ID（`docs/trace_map.md`）
   - 内容: 追加・改名した公開関数とファイルの行を書き、`DS-FN-LOAD-CURRENT-USER` の行の修飾名の関数を変えず、テンプレートには行を作らない
   - 完了条件: `bash scripts/isdd/check.sh` の対応表の検査が通ること（タスク 8 で確認）

## 2. テスト

6. **単体テストの追加**（`tests/unit/test_units.py`）
   - 対象: タスク 1〜3 の関数（上の完了条件どおり）
   - 完了条件: `.venv/bin/python -m unittest discover -s tests/unit` が全件合格

7. **E2E の追加**（`e2e/test_equipment_ledger.py` の `EquipmentLedgerE2E` に、`docs/trace_map.md` の `DS-TS-*` の名前で 8 件を足す）
   - `DS-TS-LIST-ACCOUNTS`、`DS-TS-CHANGE-ACCOUNT-ROLE`、`DS-TS-KEEP-ONE-MANAGER`、`DS-TS-RESET-ACCOUNT-PASSWORD`、`DS-TS-DELETE-ACCOUNT`、`DS-TS-NO-DELETE-BORROWING-ACCOUNT`、`DS-TS-MEMBER-AND-GUEST-CANNOT-MANAGE-ACCOUNTS`、`DS-TS-DEMOTED-MANAGER-LOSES-ACCESS`
   - 完了条件: 変更要件定義書 7 章の各場面の期待結果を、テストが確かめていること
   - 段 1・2 の E2E も全件通すこと。`python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` で JUnit XML を出す

## 3. 確認と後始末

8. **対応表とチェックの確認**
   - `bash scripts/isdd/check.sh` を実行し、エラーが無いこと。警告は報告に含める
   - 完了条件: check.sh がエラー 0 件

9. **実装後レビュー（isdd-build）**
   - 変更要件定義書と変更設計書を正本に反映し（`docs/requirements.md`・`docs/detail_design.md`）、`docs/active_change` を消す。対応表（`docs/trace_map.md`）と、要件・設計・コードの整合を逆引きで確かめる
   - 完了条件: `docs/active_change` が無く、正本が実装どおりであること。`rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が合格すること

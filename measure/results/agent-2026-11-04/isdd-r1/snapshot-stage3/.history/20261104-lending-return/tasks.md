# タスク一覧: 備品の貸出と返却（段 2・変更フロー）

入力: `.history/20261104-lending-return/change_detail_design.md`（[追加] と [削除] の設計 ID）と `change_requirements.md`。
正本（`docs/requirements.md`・`docs/detail_design.md`）は実装の中で書き換えない。反映は実装後レビューが行う。
各タスクの完了条件を満たしてから次へ進む。テスト実行コマンドは変更設計書 8-1 と 8-4 のものを使う。
段 1 の機能（アカウント、ログイン、備品の登録・修正・削除、一覧）を壊さないこと。契約は `contract.md`（段 2 の追加分を含む）。

## 0. 導入確認（固定）

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が存在する。`scripts/isdd/VERSION` の値と isdd-build の版を比べ、違えば `isdd-setup` を再実行する。依存の規則は変更設計書 7 章（段 1 の規則に、`app/loans.py` の規則を足したもの）を `scripts/isdd/dependencies.json` に書き写す
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（サーバー）・認証（有り）・外部連携（無し）が正本と一致していること

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-lending-return/` を指していることを確認する
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-lending-return/change_requirements.md .history/20261104-lending-return/change_detail_design.md --base docs/requirements.md` が合格すること

## 1. 実装（設計 ID ごと）

1. **DB の拡張（テーブルの作成と版番号の列の移行）**
   - 実装する設計 ID: `DS-SC-EQUIPMENT-WITH-REVISION`（備品の版番号の列）、`DS-SC-LOAN`（貸出の記録のテーブル）、`DS-FN-INIT-SCHEMA`（既存の関数の変更。`loans` の作成と、`revision` 列が無い既存 DB への列の追加）、`DS-FN-CONNECT-DB`（外部キーの検査を有効にする）
   - 内容: `equipment` に `revision INTEGER NOT NULL DEFAULT 1`。`loans` は `id`、`equipment_id`（UNIQUE、`equipment.id` を参照）、`account_id`（`accounts.id` を参照）、`lent_on`（TEXT）。段 1 の DB を開いたとき、`revision` が無ければ列を足し、`loans` が無ければ作る
   - 完了条件: 一時ディレクトリで初期化を 2 回行ってもエラーにならないこと。段 1 の形の DB（`revision` 列なし）に対して初期化すると列が足され、既存の備品の `revision` が 1 になること

2. **入力の検査（貸出）**
   - 実装する設計 ID: `DS-FN-VALIDATE-LOAN-INPUT`
   - 内容: 借りる社員（空、または存在しない ID は「借りる社員を選んでください」を `id_borrower` に）、貸出日（YYYY-MM-DD 形式でなければ「貸出日は YYYY-MM-DD の形式で入力してください」、今日より後なら「貸出日に未来の日付は入力できません」を `id_lent_on` に）。今日の日付は引数で受ける
   - 完了条件: 単体テストで、借りる社員の未選択、今日・過去・明日の境界、形式の誤りが確かめられること

3. **備品の取得・修正・削除（版番号と貸出の確認）**
   - 実装する設計 ID: `DS-FN-GET-EQUIPMENT-WITH-REVISION`（取得の関数。版番号を含める）、`DS-FN-UPDATE-EQUIPMENT-IF-CURRENT`（版番号が一致したときだけ更新し、版番号を 1 増やす。不一致・削除済みは保存しない。貸出の記録には触れない）、`DS-FN-DELETE-EQUIPMENT-IF-NOT-LOANED`（貸出中なら削除しない。結果を返す）。いずれも BEGIN IMMEDIATE のトランザクションで行う
   - 内容: 段 1 の `DS-MD-EQUIPMENT` の中で、同じ名前の関数を置き換える（`DS-FN-GET-EQUIPMENT`、`DS-FN-UPDATE-EQUIPMENT`、`DS-FN-DELETE-EQUIPMENT` と `DS-FN-LIST-EQUIPMENT` は削除する）。登録（`DS-FN-CREATE-EQUIPMENT`）は変更しない
   - 完了条件: 単体テストで、版番号一致の更新、不一致の拒否、削除後の拒否、管理番号の重複（自分を除く）、貸出中の削除の拒否、修正しても貸出の記録が残ること

4. **貸出の業務（貸出の登録・返却・貸出状況の一覧）**
   - 実装する設計 ID: `DS-MD-LOANS`（`app/loans.py`）、`DS-FN-REGISTER-LOAN`、`DS-FN-RETURN-LOAN`、`DS-FN-LIST-LOAN-STATUS`
   - 内容: 変更設計書 3-2 の手順どおり。貸出の登録は BEGIN IMMEDIATE で備品と社員と既存の貸出を確かめ、無ければ記録する（一意制約の違反も「既に貸出中」）。返却は貸出の記録を削除し、件数 0 件なら「既に返却済み」。貸出状況の一覧は管理番号の昇順で、貸出の記録と借りている社員の名前を結ぶ（空きの行は名前と日付が空）。`app/loans.py` は flask と werkzeug と views と auth を読まない
   - 完了条件: 単体テストで、空きへの登録、貸出中への登録の拒否、備品が無い場合、返却、既に返却済み、一覧の状況と順序が確かめられること

5. **画面と templates（貸出）**
   - 実装する設計 ID: `DS-FN-SHOW-LOAN-FORM`、`DS-FN-SUBMIT-LOAN-FORM`、`DS-FN-SUBMIT-RETURN`、`DS-IF-LOAN-REGISTER-SCREEN`、`DS-IF-LOAN-STATUS-SCREEN`（貸出状況の表の列の中身と、担当者の行の「貸出」「返却」のボタン。返却は `window.confirm` を通す）、`DS-FN-SHOW-LOAN-STATUS`（既存の関数。貸出状況の一覧を `DS-FN-LIST-LOAN-STATUS` の結果で描く）、`DS-FN-SUBMIT-EQUIPMENT-DELETE`（削除の拒否の知らせを足す）
   - 内容: 貸出の登録画面は `/equipment/<管理番号>/loan/`（GET と POST）。`id_borrower`（select、選択肢は「名前（社員番号）」）、`id_lent_on`（既定は日本時間の今日、固定オフセット +09:00 で求める）、`.lending-equipment`、「登録」ボタン。返却は POST `/equipment/<管理番号>/return/`。担当者以外は貸出状況へ戻して `.message`、未ログインはログイン画面へ（既存の `DS-FN-REQUIRE-MANAGER` を使う）。契約の要素と文言に従う
   - 完了条件: 貸出の登録画面と貸出状況の画面が GET で応答し、契約の要素（`id_borrower`、`id_lent_on`、`.lending-equipment`、「登録」「貸出」「返却」）が出ること

6. **備品の修正画面と保存（版番号の隠し項目と開き直し）**
   - 実装する設計 ID: `DS-FN-SUBMIT-EQUIPMENT-FORM`（修正の保存で版番号を渡し、他の担当者の更新・削除なら修正画面に `.error` を出して保存しない。入力値は残す）、`DS-FN-SHOW-EQUIPMENT-FORM`（段 1 の既存の関数。版番号を隠し項目に入れる。`DS-FN-GET-EQUIPMENT-WITH-REVISION` を使う）
   - 完了条件: 修正画面に版番号の隠し項目があり、他の担当者の更新後の保存が `.error` で拒否されること

7. **削除の要求と貸出中の拒否**
   - 実装する設計 ID: `DS-FN-SUBMIT-EQUIPMENT-DELETE`（段 1 の既存。貸出中の拒否の知らせ「この備品は貸出中のため削除できません。先に返却を処理してください」を `.message` に出す）、`DS-FN-DELETE-EQUIPMENT-IF-NOT-LOANED` を使う
   - 完了条件: 貸出中の備品の削除が拒否され、行が残ること

8. **アプリの登録と起動（貸出の画面を足す）**
   - 実装する設計 ID: `DS-MD-VIEWS`（既存の画面の入口。貸出の 3 つの画面の関数を登録する）、`DS-MD-VALIDATION`（既存。貸出の検査を足す）、`DS-MD-APP-FACTORY`（既存。変更なし）、`DS-MD-SERVER`（既存。変更なし）
   - 完了条件: `bash run.sh` で起動し、`/` と `/equipment/<管理番号>/loan/` が応答すること

9. **単体テストの追加**
   - 実装する設計 ID: なし（8-1 の単体テスト。対応表の粒度は関数で、テストファイルは対応表に載せない）
   - 内容: `tests/unit/` に、タスク 2〜4 の関数と版番号の確認の単体テストを足す（段 1 の単体テストも残す。段 1 の `DS-FN-LIST-EQUIPMENT` などを参照していれば新しい関数に書き換える）
   - 完了条件: `.venv/bin/python -m unittest discover -s tests/unit` が全件通ること

10. **E2E テストの追加**
    - 実装する設計 ID: 変更設計書 8-2 の `DS-TS-REGISTER-LOAN`、`DS-TS-LOAN-INPUT-VALIDATION`、`DS-TS-NO-DOUBLE-LOAN`、`DS-TS-RETURN-EQUIPMENT`、`DS-TS-NO-DOUBLE-RETURN`、`DS-TS-NO-DELETE-LOANED-EQUIPMENT`、`DS-TS-EDIT-KEEPS-LOAN`、`DS-TS-EDIT-CONFLICT-REJECT`、`DS-TS-MEMBER-AND-GUEST-CANNOT-LOAN-OR-RETURN`、`DS-TS-VIEW-LOAN-DETAILS-AS-GUEST`、`DS-TS-CONCURRENT-RESPONSE-TIME`（11 件。テスト関数名は `test_` で始め、設計 ID を小文字・アンダースコアにした名前）
    - 内容: `e2e/` に 11 件の unittest のテスト関数を足す。同時の貸出・返却は、標準ライブラリのスレッドを 2 本（同時に送るため Barrier を使う）で送る。50 件の同時表示は、500 件の備品を登録してから 50 スレッドで `/` を開き、各応答時間を測る。段 1 の 16 件は残す。`SESSION_IDLE_TIMEOUT_SECONDS` の別サーバーは段 1 のとおり
    - 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` が全件通ること

11. **README.md の更新**
    - 実装する設計 ID: `DS-OP-FIRST-ACCOUNT-SETUP`（既存。変更なし）
    - 内容: 貸出と返却の使い方（担当者が貸出の登録と返却を行う。社員と未ログインの人は貸出状況で確かめられる）を README に 1 段落足す。段 1 の起動方法は残す
    - 完了条件: README.md を読むだけで、初回起動と貸出の登録の仕方が分かること

## 2. 実装完了確認（固定）

1. **対応表（docs/trace_map.md）更新タスク**
   - 変更設計書 7 章の [追加] と [削除] に従って `docs/trace_map.md` を書き換える（`DS-MD-LOANS`、新しい `DS-FN-*`、`DS-SC-*`、`DS-IF-LOAN-REGISTER-SCREEN`。[削除] の関数と `DS-SC-EQUIPMENT` の行は消す）。`DS-TS-*` は `e2e/` のテスト関数に結ぶ
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること（進行中の変更の行を含む）

2. **起動確認タスク**
   - 変更設計書 9 章の方法（段 1 と同じ）で `bash setup.sh` と `bash run.sh` を実行し、`/` が応答すること
   - 完了条件: 起動がエラーなく完了すること

3. **単体テスト全件通過タスク**
   - `.venv/bin/python -m unittest discover -s tests/unit` を実行する
   - 完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返す

4. **E2E テスト全件通過タスク**
   - `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` を実行する（段 1 の 16 件と追加の 11 件）
   - 完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返し、全件通過まで続ける

5. **README.md 記載タスク**
   - 貸出と返却の使い方が README.md にあること
   - 完了条件: README.md を読むだけで、貸出の登録と返却の仕方が分かること

6. **実装完了チェックタスク**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する
   - 完了条件: 全項目が OK であること

## 3. 補足（変更の記録）

- 要件の見直し: なし（[削除] の要件は無い）。
- 除外要件: なし。

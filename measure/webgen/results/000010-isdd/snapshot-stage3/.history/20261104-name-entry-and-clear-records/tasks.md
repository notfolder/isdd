# tasks.md: 利用者名の表示と抽選記録の一括削除

対象: `change_requirements.md`・`change_detail_design.md`（同じディレクトリ）。isdd-build が上から順に実行する。
正本（`docs/requirements.md`・`docs/detail_design.md`）は、実装後レビューで反映するまで書き換えない。
実装は既存の機能を壊さないこと（抽選、景品一覧、景品の追加と削除、抽選記録の追加と検索、利用者名の検証、メニュー移動、配色）。

## 0. 固定タスク（実装開始前）

0-1. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が存在する。`scripts/isdd/completeness.json` の実行形態（サーバー）・認証（無し）・外部連携（無し）が設計書第 1 章・第 9 章と一致していることを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` が実行できること。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-name-entry-and-clear-records/` であることを確かめる。
   - 完了条件: `python3 .claude/skills/isdd-spec/scripts/rq_ds_link_checker.py .history/20261104-name-entry-and-clear-records/change_requirements.md .history/20261104-name-entry-and-clear-records/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 実装タスク

1. **抽選記録の検索と全件削除（データアクセス）**
   - 実装する設計 ID: `DS-FN-FIND-RECORDS-WITH-NAME`（`app/repository.py::find_records_by_name`、`DS-MD-REPOSITORY`）、`DS-FN-DELETE-ALL-RECORDS`（`app/repository.py::delete_all_records`）
   - 内容: `find_records_by_name` は `id`・`player_name`・`prize_name`・`spun_at` の辞書を、`spun_at` の新しい順に返す（利用者名の完全一致は変えない）。`delete_all_records(db_path)` は `spin_record` の全件を 1 つの `DELETE` で削除し、削除件数を返す。`prize` 表は触らない。
   - 完了条件: 単体テストで、検索結果に `player_name` が入ること、`delete_all_records` が件数を返し、その後の検索が空になること、景品（`list_prizes`）が残ることを確かめる。

2. **抽選記録の一括削除の API（HTTP サーバー）**
   - 実装する設計 ID: `DS-FN-HANDLE-CLEAR-RECORDS`、`DS-IF-CLEAR-RECORDS-API`（`app/server.py::handle_clear_records`、`DS-MD-SERVER`）。`DS-IF-RECORDS-WITH-NAME-API`（`app/server.py::handle_records`、出力の中身は `find_records_by_name` の変更に従う）
   - 内容: `DELETE /api/records` は 200 と `deleted`（件数）を返す。失敗は 500（`Something went wrong. Please try again.`）。`do_DELETE` の振り分けに `/api/records` を加える（`/api/prizes/{id}` の扱いは変えない）。`/api/records` の `POST` や他の組み合わせは 404。`GET /api/records?player_name=` の応答は、各記録に `player_name` が増える以外は変えない。
   - 完了条件: ハンドラの単体テストで、200 と件数、404 の組み合わせを確かめる。既存の API（`/api/spin`・`/api/prizes`・`/api/records` の GET）の応答が変わらないこと。

3. **利用者名の検証の確認（業務ロジック）**
   - 実装する設計 ID: `DS-FN-VALIDATE-PLAYER-NAME`（`app/validation.py`、変更なし）、`DS-FN-HANDLE-SPIN`（`app/server.py`、変更なし）
   - 内容: 既存の検証（前後の空白を除いて 1〜30 文字）を変えない。`RQ-FT-SPIN-REQUIRES-NAME` の確認だけをする。
   - 完了条件: 単体テストで、空、空白だけ、31 文字の拒否と、`handle_spin` が 400 を返し記録を作らないことを確かめる。

4. **画面の表示と一括削除（HTML と JavaScript）**
   - 実装する設計 ID: `DS-MD-INDEX-HTML`（My Records の表に利用者名の列 `Player` を加える。表の列は Player、Prize、Date and time。Clear records ボタンと、成功の文言の欄 `records-status` を加える）、`DS-MD-APP-JS`、`DS-FN-RENDER-RECORDS`（`static/app.js::renderRecords`、検索の結果から表を描く。利用者名・景品名・日時の 3 列）、`DS-FN-CLEAR-RECORDS`（`static/app.js::clearRecords`、確認ダイアログ、`DELETE /api/records`、表を空にして文言を出す。Cancel なら何もしない。失敗は `records-error` に `Something went wrong. Please try again.`）、`DS-FN-REMEMBER-PLAYER-NAME`（変更なし）、`DS-FN-VALIDATE-PLAYER-NAME`（変更なし）
   - 内容: 確認ダイアログの文言は `Delete all winning records? This cannot be undone.`。成功の文言は `All winning records were deleted.`。すべての文言は英語。Clear records ボタンは既存のボタンの配色（濃い緑、文字は白）に従う。
   - 完了条件: 画面の HTML に `Clear records` のボタンと `Player` の列があること。`app.js` で `window.confirm` を呼ぶこと。

5. **既存の E2E と単体テストの更新**
   - 内容: `e2e/test_e2e.py` の `test_spin_and_record`（`DS-TS-SPIN-AND-RECORD-V2-E2E`）、`test_validate_player_name`（`DS-TS-VALIDATE-PLAYER-NAME-V2-E2E`）、`test_view_own_records`（`DS-TS-VIEW-OWN-RECORDS-V2-E2E`）の期待を、変更後の表（利用者名の列、回す前の必須）に合わせる。新しい `test_clear_records`（`DS-TS-CLEAR-RECORDS-E2E`）を加える。確認ダイアログは、テストの自動化で OK と Cancel の両方を扱う。
   - 完了条件: 4 本の E2E が変更後の振る舞いを確かめること。

## 2. 実装完了時の固定タスク

6. **対応表（docs/trace_map.md）更新タスク**
   - 変更設計書 第 11 章の `DS-*` の [追加] を対応表に加え、[削除] の行を外す（`DS-FN-FIND-RECORDS-BY-NAME`、`DS-IF-RECORDS-API`、`DS-TS-SPIN-AND-RECORD-E2E`、`DS-TS-VALIDATE-PLAYER-NAME-E2E`、`DS-TS-VIEW-OWN-RECORDS-E2E` の行を除く）。新しい関数（`handle_clear_records`、`delete_all_records`、`renderRecords`、`clearRecords`）と E2E の 3 本（V2）と 1 本（CLEAR）を登録する。E2E の行は `e2e/test_e2e.py` の関数名に結ぶ。
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

7. **起動確認タスク**
   - `bash setup.sh` の後、`PORT=<空きポート> DATA_DIR=<一時ディレクトリ> bash run.sh` で起動し、Spin（名前が空だと回らない）、My Records（名前列、Clear records と確認）、Prizes、Manage prizes の画面が開けること、サンプル景品 6 件が出ることを確かめる。
   - 完了条件: 起動がエラーなく完了し、画面が応答すること。確認後に、自分が起動したサーバーの PID だけを止める。

8. **単体テスト全件通過タスク**
   - 完了条件: `python3 -m unittest discover -s tests` の FAIL が 0 件。

9. **E2E テスト全件通過タスク**
   - 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` の FAIL が 0 件。

10. **実装完了チェックタスク**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行し、全項目が OK であること。

11. **実装後レビュー（isdd-build）タスク**
   - 変更を正本（`docs/requirements.md`・`docs/detail_design.md`）へ反映し、`docs/trace_map.md` と合わせる。`[削除]` の要件・設計を正本から外し、`docs/active_change` を消す。`rq_integrity_checker.py docs/requirements.md` と `rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が合格すること。README の My Records と Clear records の説明を更新する。
   - 完了条件: `docs/active_change` が無い。正本の検査が合格。`bash scripts/isdd/check.sh --strict` が通る。

## 3. 実装中に決めたこと（補足）

- 変更の要件 ID・設計 ID は `change_requirements.md`・`change_detail_design.md` のとおり。実装中に ID を作らない。
- 「回す前に名前が必須」は既存の動作。新しい検証の処理は増やさない。
- 一括削除は、利用者名に関係なくすべての抽選記録を消す。景品は消さない。確認は `window.confirm` を使い、確認の画面は作らない。

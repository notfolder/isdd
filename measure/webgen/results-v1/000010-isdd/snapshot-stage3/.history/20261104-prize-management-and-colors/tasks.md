# tasks.md: 配色の変更と景品管理ページの追加

対象: `change_requirements.md`・`change_detail_design.md`（同じディレクトリ）。isdd-build が上から順に実行する。
正本（`docs/requirements.md`・`docs/detail_design.md`）は、実装後レビューで反映するまで書き換えない。
実装は既存の機能を壊さないこと（抽選、景品一覧、抽選記録、利用者名の検証、メニュー移動）。

## 0. 固定タスク（実装開始前）

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が存在する（導入済み）。`scripts/isdd/completeness.json` の実行形態（サーバー）・認証（無し）・外部連携（無し）が設計書第 1 章・第 9 章と一致していることを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、`completeness.json` の値が上の内容と一致すること。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-prize-management-and-colors/` であることを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-spec/scripts/rq_ds_link_checker.py .history/20261104-prize-management-and-colors/change_requirements.md .history/20261104-prize-management-and-colors/change_detail_design.md --base docs/requirements.md` が合格すること（isdd-build に同梱の版があればそれを使う）。

## 1. 実装タスク

1. **景品の追加と削除（データアクセス）**
   - 実装する設計 ID: `DS-FN-INSERT-PRIZE`、`DS-FN-DELETE-PRIZE`（`app/repository.py`、`DS-MD-REPOSITORY`）
   - 内容: `insert_prize(db_path, name)` は景品を 1 件追加し、`id`・`name`・`description`（空文字）の辞書を返す。`delete_prize(db_path, prize_id)` は景品を 1 件削除し、削除件数（0 か 1）を返す。抽選記録は消さない。外部キーの有効化（`PRAGMA foreign_keys`）は書かない。
   - 完了条件: 単体テストで、追加した景品が `list_prizes` に出ること、削除で件数 1 が返り、0 件の ID は 0 が返ること、抽選記録（`insert_spin_record` で作った記録）が削除の後も `find_records_by_name` で残ることを確かめる。

2. **景品名の検証（業務ロジック）**
   - 実装する設計 ID: `DS-FN-VALIDATE-PRIZE-NAME`（`app/validation.py`、`DS-MD-VALIDATION`）
   - 内容: 前後の空白を除いて 1〜60 文字。文字列でない、空、空白だけ、60 文字超は `ValueError`（文言は `Please enter a prize name (1–60 characters).`）。
   - 完了条件: 単体テストで、正常な名前（前後の空白を除いた値を返す）、空、空白だけ、61 文字の拒否を確かめる。

3. **景品の追加と削除の API（HTTP サーバー）**
   - 実装する設計 ID: `DS-FN-HANDLE-ADD-PRIZE`、`DS-FN-HANDLE-DELETE-PRIZE`、`DS-IF-ADD-PRIZE-API`、`DS-IF-DELETE-PRIZE-API`（`app/server.py`、`DS-MD-SERVER`）
   - 内容: `POST /api/prizes` は 201 と `prize`、不正は 400（`Please enter a prize name (1–60 characters).`）、JSON 不正は 400（`Invalid request`）、失敗は 500（`Something went wrong. Please try again.`）。`DELETE /api/prizes/{id}` は 200 と `deleted_id`、景品が無いか ID が整数でなければ 404（`Prize not found`）。`/api/prizes` の `GET` は変えない。他の組み合わせは 404。
   - 完了条件: 実サーバーで E2E（実装後のタスク 4 で確かめる）に加え、ハンドラが上の応答を返すことを単体で確かめる。既存の API（`/api/spin`・`/api/records`・`/api/prizes` の GET）の応答が変わらないこと。

4. **画面の配色（スタイル）**
   - 実装する設計 ID: `DS-MD-STYLE-CSS`（`static/style.css`）
   - 内容: 背景はアイボリー（`#FFFFF0`）。ヘッダー、ボタン、カード（`.panel`）、表の見出し、ホイールの区画に濃い緑（`#006400`）。濃い緑の部品の上の文字は白。薄いグレーと濃い赤は使わない（既存の配色の値を置き換える）。
   - 完了条件: `static/style.css` に `#FFFFF0` と `#006400` があり、旧い色（薄いグレーの背景、濃い赤の部品）が残っていないこと（`grep` で確かめる）。

5. **画面の構成と景品管理（HTML と JavaScript）**
   - 実装する設計 ID: `DS-MD-INDEX-HTML`（`static/index.html`）、`DS-MD-APP-JS`（`static/app.js`）、`DS-FN-SHOW-VIEW-AND-RELOAD`（`showView` を改名して中身を変える。旧 `DS-FN-SHOW-VIEW` は削除）、`DS-FN-RENDER-MANAGE-PRIZES`、`DS-FN-RENDER-WHEEL`（変更なし）、`DS-IF-STATIC-PAGE`（変更なし）
   - 内容:
     - 共通メニューを Spin、Prizes、My Records、Manage prizes の 4 項目にする（`#/manage`）。現在の画面の項目に `aria-current` を付ける。
     - Manage prizes 画面（`#view-manage`）: 景品名の入力欄、Add ボタン、エラー欄（`role="alert"`）、景品の表（Prize、Description、Remove）、0 件のときの `No prizes yet`。見出しは `Manage prizes`。
     - 画面を開くたびに `GET /api/prizes` を読み、Prizes の表、Manage prizes の表、ホイールを描き直す（`DS-FN-SHOW-VIEW-AND-RELOAD`）。読み込み失敗は Spin 画面のエラー欄に出す。
     - Add は `POST /api/prizes`、Remove は `DELETE /api/prizes/{id}` を呼び、成功したら一覧を読み直す。Add 成功後は入力欄を空にする。
     - ホイールの区画の色は `SEGMENT_COLORS` を濃い緑の系統（例: `#006400`、`#1b5e20`、`#004d00`、`#2e7d32`）に変える。
     - 景品名と説明は `textContent` で入れる。画面の文言はすべて英語。
   - 完了条件: ブラウザで（または E2E と目視で）4 画面を開けること、Add と Remove が表とホイールに反映されること、既存の抽選（Spin）と記録の画面が動くこと。

6. **E2E テストの更新（e2e/test_e2e.py）**
   - 実装する設計 ID: `DS-TS-MANAGE-PRIZES-E2E`、`DS-TS-VALIDATE-PRIZE-NAME-E2E`、`DS-TS-REMOVE-PRIZE-KEEPS-RECORDS-E2E`（新規）、`DS-TS-NAVIGATE-MENU-E2E`・`DS-TS-FIRST-START-AND-THEME-E2E`（内容を変える）
   - 内容: 8-2 の [追加] と [削除] の行に従う。既存の 5 本（`DS-TS-SPIN-AND-RECORD-E2E`、`DS-TS-VALIDATE-PLAYER-NAME-E2E`、`DS-TS-VIEW-PRIZE-LIST-E2E`、`DS-TS-VIEW-OWN-RECORDS-E2E`、`DS-TS-EMPTY-PRIZES-E2E`）は変えない。
   - 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` で全件通過（FAIL 0 件）。

7. **単体テストの更新（tests/test_units.py）**
   - 内容: タスク 1 と 2 の単体テストを加える。既存のテストは変えない（壊れたら実装を直す）。
   - 完了条件: `python3 -m unittest discover -s tests` で全件通過。

8. **README.md の更新**
   - 内容: 画面の一覧に Manage prizes を加え、景品の追加と削除の操作を書く。起動方法は変えない。
   - 完了条件: README.md を読むだけで Manage prizes の使い方が分かること。

## 2. 実装完了時の固定タスク

9. **対応表（docs/trace_map.md）更新タスク**
   - 実装したファイル・関数を `docs/trace_map.md` に登録する。`DS-FN-SHOW-VIEW` の行は `DS-FN-SHOW-VIEW-AND-RELOAD`（`static/app.js::showView`）に、`DS-FN-HANDLE-ADD-PRIZE`、`DS-FN-HANDLE-DELETE-PRIZE`、`DS-FN-VALIDATE-PRIZE-NAME`、`DS-FN-INSERT-PRIZE`、`DS-FN-DELETE-PRIZE`、`DS-FN-RENDER-MANAGE-PRIZES`（`static/app.js::renderManagePrizes`）、新しい E2E の 3 本の `DS-TS` を追加する。
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

10. **起動確認タスク**
   - `bash setup.sh` の後、`PORT=<空きポート> DATA_DIR=<一時ディレクトリ> bash run.sh` で起動し、Spin、Prizes、My Records、Manage prizes の 4 画面が開けること、サンプル景品 6 件が出ること、Add と Remove が動くことを確かめる。
   - 完了条件: 起動がエラーなく完了し、4 画面が応答すること。確認後にサーバーを止める（自分が起動した PID だけ）。

11. **単体テスト・結合テスト全件通過タスク**
   - 完了条件: `python3 -m unittest discover -s tests` の FAIL が 0 件。失敗したら修正と再実行を繰り返す。

12. **E2E テスト全件通過タスク**
   - 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` の FAIL が 0 件。失敗したら修正と再実行を繰り返す。

13. **実装完了チェックタスク**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行し、全項目が OK であること。
   - 完了条件: 全項目が OK。

14. **実装後レビュー（isdd-build）タスク**
   - 変更を正本（`docs/requirements.md`・`docs/detail_design.md`）へ反映し、`docs/trace_map.md` と合わせる。`[削除]` の要件・設計を正本から外し、`docs/active_change` を消す。`rq_integrity_checker.py docs/requirements.md` と `rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が合格すること。
   - 完了条件: `docs/active_change` が無い。正本の検査が合格。`bash scripts/isdd/check.sh --strict` が通る。

## 3. 実装中に決めたこと（補足）

- 変更の要件 ID・設計 ID は `change_requirements.md`・`change_detail_design.md` のとおり。実装中に ID を作らない。
- 景品の削除は確認の画面を出さない。景品名の重複は禁じない（依頼に無いため）。

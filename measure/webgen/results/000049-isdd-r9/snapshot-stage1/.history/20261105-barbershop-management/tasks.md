# タスク: 理髪店管理ウェブサイト（2026-11-05）

入力: `docs/requirements.md`、`docs/detail_design.md`。上から順に実行する。

## 0. isdd-setup 導入確認タスク（先頭・固定）

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。実行形態 server、認証なし（D3）、外部連携なし（D2）、対応表の粒度 class（設計書 7 章）、依存の規則（設計書 7 章）を `scripts/isdd/dependencies.json` に書き写す。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が設計書と一致している。

## 1. 保存と検査（`src/core`）

- 対象: DS-MD-STORE（`src/core/db.py`）、DS-CL-STORE（`Store`）、DS-FN-SEED-SAMPLE-DATA（`Store.seed_sample_data_if_empty`）、DS-SC-BARBER-TABLE、DS-SC-SERVICE-TABLE、DS-MD-VALIDATION（`src/core/validation.py`）、DS-CL-VALIDATION-ERROR（`ValidationError`）、DS-FN-VALIDATE-BARBER-FORM、DS-FN-VALIDATE-SERVICE-FORM、DS-FN-VALIDATE-NOTIFY-FORM、DS-MD-WHATSAPP-LINK（`src/core/whatsapp.py`）、DS-FN-BUILD-WHATSAPP-LINK、DS-FN-SPLIT-PHONE-LIST。
- 完了条件: 単体テスト（`tests/`）が D7〜D9、D13、D15、D19 の規則を確かめて全件通過。

## 2. 画面と HTTP（`src/web`）

- 対象: DS-MD-VIEWS（`src/web/views.py`）、DS-IF-HOME-SCREEN、DS-IF-BARBER-LIST-SCREEN、DS-IF-BARBER-ADD-SCREEN、DS-IF-SERVICE-LIST-SCREEN、DS-IF-SERVICE-ADD-SCREEN、DS-IF-NOTIFY-SCREEN、DS-IF-PAGE-LAYOUT（`src/web/static/style.css` を含む）、DS-MD-APP-HANDLER（`src/web/app.py`）、DS-CL-APP-HANDLER（`AppHandler`）、DS-IF-HTTP-ROUTES（`AppHandler.do_GET`、`AppHandler.do_POST`）、DS-MD-SERVER-ENTRY（`src/web/server.py`）。
- 画面の文言は英語。全画面に上部メニュー（Home / Barbers / Services / Notify）。雪の背景、主色 #696969。
- 完了条件: 結合テスト（`tests/`）で全経路が期待の状態コードと HTML を返す。

## 3. 起動スクリプトと README

- 対象: DS-OP-SETUP-SH（`setup.sh`）、DS-OP-RUN-SH（`run.sh`）。PORT（既定 8000）、DATA_DIR（既定は `./data`）。
- 完了条件: `bash setup.sh` が成功し、`PORT=18080 bash run.sh` が前景で起動し、`http://127.0.0.1:18080/` が 200 を返す。

## 4. E2E テスト（`e2e/`）

- 対象: DS-TS-START-WITH-SAMPLE-DATA-E2E、DS-TS-NAVIGATE-FROM-HOME-E2E、DS-TS-BROWSE-AND-ADD-BARBER-E2E、DS-TS-BROWSE-AND-ADD-SERVICE-E2E、DS-TS-SEND-WHATSAPP-LINKS-E2E、DS-TS-REJECT-INVALID-ENTRIES-E2E、DS-TS-SNOW-AND-GRAY-THEME-E2E を `e2e/test_site.py` の同名の関数（`test_...`）に結ぶ。
- 完了条件: 設計書 8-4 の実行コマンドで全件通過。

## 5. 対応表（`docs/trace_map.md`）

- 実装したファイル・クラス・関数・DS-TS を登録する（書式は trace-map-rules.md）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 6. 起動確認

- 完了条件: `PORT=<任意> bash run.sh` で起動し、Home、Barbers、Services、Notify が開ける。サンプルが見える。

## 7. 実装完了確認（末尾・固定）

1. 対応表（docs/trace_map.md）更新タスク: 上の 5 を満たしたか確認する。完了条件は `bash scripts/isdd/check.sh --strict` が通ること。
2. 起動確認タスク: 上の 6。
3. 単体テスト・結合テスト全件通過タスク: `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"` が全件通過（FAIL 0 件）。
4. E2E テスト全件通過タスク: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` が全件通過。
5. README.md 記載タスク: 「起動方法」（setup.sh、run.sh、PORT、DATA_DIR、初期データ）を書く。認証は無いので「初期ユーザー」は書かない。
6. 実装完了チェックタスク: `python3 scripts/isdd/implementation_completeness_checker.py .` が全項目 OK。
7. 要件・設計の対応確認: `rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が問題 0 件。

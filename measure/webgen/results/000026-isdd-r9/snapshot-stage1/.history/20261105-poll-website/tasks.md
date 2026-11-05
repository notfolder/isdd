# tasks.md: 投票サイト（Polls Website）

- 入力: `docs/requirements.md`、`docs/detail_design.md`
- 実装の順序は上から。各タスクの完了条件を満たしてから次へ進む。

## 0. isdd-setup 導入確認タスク（固定）

- 実装する設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。導入時の指定: 実行形態 = サーバー（ローカル）、認証 = 無し、外部連携 = 無し、対応表の粒度 = `class`、ソースのディレクトリ = `app`、依存の規則 = 無し（`scripts/isdd/dependencies.json` は空の規則）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致する。

## 1. 起動スクリプト（setup.sh・run.sh）と設定

- 実装する設計 ID: DS-OP-SETUP-SCRIPT, DS-OP-RUN-SCRIPT, DS-OP-ENV-VARS, DS-MD-CONFIG
- 内容
  - `setup.sh`: Python 3.12 を確認、`DATA_DIR`（既定 `./data`）を作成、`requirements-dev.txt`（pytest、playwright）を pip で入れ、`python3 -m playwright install chromium` を実行する。
  - `run.sh`: `PORT`（既定 8000）と `DATA_DIR`（既定 `./data`）を読み、`exec python3 app/server.py` で前面起動する。
  - `app/config.py`: `PORT`・`DATA_DIR` を読む関数を置く。
- 完了条件: `bash setup.sh` が正常終了する。`PORT=8123 bash run.sh` で `http://127.0.0.1:8123/` が応答する。
- 検証: `bash setup.sh; echo $?`、`PORT=8123 bash run.sh &` の後に `curl -sI http://127.0.0.1:8123/polls`。

## 2. データ層（db.py）

- 実装する設計 ID: DS-MD-DATABASE, DS-CL-DATABASE, DS-SC-DATABASE-FILE, DS-SC-POLL-TABLE, DS-SC-OPTION-TABLE, DS-SC-VOTE-TABLE
- 内容: `Database` クラス（接続、スキーマ作成は `CREATE TABLE IF NOT EXISTS`、`UNIQUE(poll_id, voter_token)`）。`DATA_DIR` が無ければ作る。
- 完了条件: 一時 DATA_DIR で起動時にスキーマが作られ、2 回目の起動でも失敗しない。

## 3. サンプルデータ（seed.py）

- 実装する設計 ID: DS-MD-SEED, DS-CL-SAMPLE-SEEDER（要件 RQ-OP-SAMPLE-DATA に対応）
- 内容: 投票が 0 件のとき、要件の 3 件（Favorite season?、Best programming language for beginners?（票 0 件）、Preferred lunch?）と選択肢と票を入れる。
- 完了条件: 空の DATA_DIR で起動すると投票 3 件が見え、「Best programming language for beginners?」の票が 0 件。

## 4. 業務処理（polls.py）

- 実装する設計 ID: DS-MD-POLLS, DS-CL-POLL-SERVICE
- 内容: `PollService` の `list_polls`、`get_poll`、`cast_vote`（未選択・選択肢不正・投票済み・成功を結果で返す）、`get_results`（票数と割合、合計）、`list_results`。
- 完了条件: 単体テスト（タスク 7）が通る。

## 5. 画面（views.py）

- 実装する設計 ID: DS-MD-VIEWS, DS-IF-POLL-LIST-SCREEN, DS-IF-POLL-VOTE-SCREEN, DS-IF-POLL-RESULTS-SCREEN, DS-IF-RESULTS-LIST-SCREEN
- 内容: 共通メニュー（Polls、Results）、各画面の HTML。CSS は背景 #ffffff、部品 #000080。文言は英語。JavaScript は使わない。HTML はエスケープする。
- 完了条件: 4 画面と 404 画面の HTML が出る（タスク 6 の E2E で確かめる）。

## 6. HTTP 経路（server.py）

- 実装する設計 ID: DS-MD-SERVER, DS-CL-REQUEST-HANDLER, DS-IF-ROOT-REDIRECT, DS-IF-POLL-VOTE-SUBMIT
- 内容: `ThreadingHTTPServer` を `127.0.0.1:$PORT` で起動。`/` → 302 `/polls`。`/polls`、`/polls/{id}`、`POST /polls/{id}/vote`、`/polls/{id}/results`、`/results`。Cookie `voter`（英数字 32 文字、HttpOnly）を発行。未知の経路は 404。
- 完了条件: `curl` で各経路が期待のステータスを返す。

## 7. 単体テスト（DS-TS-UNIT-POLL-SERVICE）

- 実装する設計 ID: DS-TS-UNIT-POLL-SERVICE
- 内容: `e2e/test_polls_unit.py`（一時 DB を使う。テストは e2e 配下に置く）。未選択、選択肢不正、投票済み、成功、割合の計算を確かめる。
- 実行コマンド: `.venv/bin/python -m pytest e2e/test_polls_unit.py`
- 完了条件: FAIL が 0 件。

## 8. E2E テスト（DS-TS-*-E2E）

- 実装する設計 ID: DS-TS-BROWSE-AND-VOTE-E2E, DS-TS-VOTE-WITHOUT-SELECTION-E2E, DS-TS-ONE-VOTE-E2E, DS-TS-RESULTS-LIST-E2E, DS-TS-UNKNOWN-POLL-E2E, DS-TS-VISUAL-STYLE-E2E, DS-TS-EMPTY-RESULTS-E2E
- 内容: `e2e/conftest.py`（一時ポートと一時 DATA_DIR でサーバーを起動）、`e2e/test_site.py`（各 DS-TS を 1 関数に対応させる。関数名は `test_` + 下線の名前）。Playwright（Chromium）で操作する。
- 実行コマンド: `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`
- 完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返す。

## 9. README.md

- 内容: 起動方法（`bash setup.sh`、`PORT=8000 bash run.sh`）、画面の説明、テストの実行方法。
- 完了条件: README を読むだけで起動できる。

## 10. 対応表の登録（固定）

- 内容: 実装したファイル・クラス・関数を `docs/trace_map.md` に登録する（`isdd-build` の trace-map-rules.md の書式）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 11. 起動確認（固定）

- 内容: `bash setup.sh` の後、`PORT=任意 bash run.sh` で起動し、ブラウザで `/`、`/polls`、`/results` が開けることを確かめる。確認後、起動した PID だけを止める。
- 完了条件: 起動がエラーなく続き、主要な画面が開く。

## 12. 単体・E2E の全件通過（固定）

- 完了条件: タスク 7 と 8 の全件が通る。

## 13. 実装完了チェック（固定）

- 内容: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

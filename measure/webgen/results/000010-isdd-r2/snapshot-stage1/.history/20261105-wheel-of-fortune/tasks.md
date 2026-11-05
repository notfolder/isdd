# 実装タスク: Wheel of Fortune（ホイール抽選の Web サイト）

入力: `docs/requirements.md`、`docs/detail_design.md`（新規フロー）。上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。`--src app --runtime server --no-auth --no-external --e2e-dir e2e --granularity function` を渡す。`scripts/isdd/dependencies.json` には詳細設計書 7-4 の依存の規則を書き写す。
- 完了条件: `bash scripts/isdd/check.sh` が実行できる。`scripts/isdd/completeness.json` の実行形態（server）・認証（無し）・外部連携（無し）が詳細設計書と一致する。

## 1. 基盤（起動スクリプト）

1.1 `setup.sh` と `run.sh` を作る（詳細設計書 9-1）。`run.sh` は `PORT`（既定 8000）と `DATA_DIR`（既定 `data`）を決め、`python3 -m app` を前景で実行する。`setup.sh` は Python 3.9 以上を確かめる。
- 完了条件: `bash setup.sh` が成功し、`PORT=8123 bash run.sh` で起動する。

1.2 `.gitignore` に `data/`、`__pycache__/` を入れる（`isdd-setup` が `e2e/results/` を足す）。

## 2. データ層（`app/database.py`）

2.1 `Database` クラスを作る。`initialize`（表の作成、景品が空のときだけ景品 6 件と当選記録のサンプル 3 件を 1 トランザクションで入れる）、`list_prizes`（表示順、景品ID の昇順）、`add_winning_record`（UTC の ISO 8601 の当選日時で 1 件追加し、記録を返す）、`list_winnings_by_name`（`COLLATE NOCASE` の完全一致、当選日時と記録IDの降順）。SQL はすべてパラメータで渡す。
- 完了条件: 単体テスト（tests/test_database.py）が全件通過。

## 3. 業務ロジック（`app/service.py`）

3.1 `RequestError`、`validate_player_name`、`SpinService`（`get_prizes`、`spin`、`get_winnings`）を作る。`SpinService` は乱数の源を注入できるようにする。
- 完了条件: 単体テスト（tests/test_service.py）が全件通過。

## 4. HTTP 層（`app/server.py`、`app/__main__.py`）

4.1 `create_server(host, port, service)` と `WheelRequestHandler` を作る。`do_GET`/`do_POST` で `/`、`/prizes`、`/my-winnings`（serve_page）、`/static/`（serve_static）、`/api/prizes`（handle_prizes）、`/api/winnings`（handle_winnings）、`/api/spins`（handle_spin）に振り分ける。想定外の例外は 500 と標準エラー出力にする。範囲外の静的パスは 404。

4.2 `app/__main__.py` の `main` で `PORT` を読み（不正なら終了コード 2）、`DATA_DIR` を決めて作り、`Database` を初期化し、`SpinService` と `create_server("127.0.0.1", PORT, service)` を組み立て、`serve_forever` で前景実行する。
- 完了条件: `PORT=8123 bash run.sh` で起動し、`curl` で API と画面が返る。確認後に自分が起動したプロセスを PID で止める。

## 5. 画面（`web/`）

5.1 `web/index.html`、`web/prizes.html`、`web/my-winnings.html`（共通のヘッダーと 3 つのリンク。開いている画面に `aria-current="page"`）。
5.2 `web/static/style.css`（背景 `#D3D3D3`、部品 `#8B0000`）。
5.3 `web/static/common.js`、`spin.js`（ホイール描画と回転、名前の検査、抽選の要求）、`prizes.js`、`my-winnings.js`（名前で絞り込み、表示）。動的な文字は `textContent` で入れる。
- 完了条件: 4 つの JavaScript が `node --check` を通る。3 画面と CSS・JS が 200 で返る。

## 6. テスト

6.1 `e2e/test_wheel_site.py` の `WheelSiteTest` に、詳細設計書 8-2 の 8 シナリオを 1 対 1 のメソッドで書く。
- 完了条件: 8-4 の実行コマンドで全件通過。`e2e/results/e2e.xml` が出る。

## 7. 対応表（docs/trace_map.md）

7.1 実装したファイル、クラス、公開関数・メソッドを `docs/trace_map.md` に登録する（粒度 function）。E2E の `DS-TS` は `e2e/test_wheel_site.py::WheelSiteTest.<メソッド名>` に結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 8. 実装後レビュー（isdd-build 段階 2）と最終確認

8.1 `implementation_completeness_checker.py` が全項目 OK。
8.2 README.md を書く（「起動方法」: `bash setup.sh`、`PORT=8000 bash run.sh`、保存先の `DATA_DIR`。認証は無いので初期ユーザーは書かない）。
8.3 起動確認: `PORT=任意 bash run.sh` で起動し、3 画面が開けることを HTTP で確かめる。確認後、自分が起動したプロセスを PID で止める。
8.4 実装後レビュー: 正本（`docs/requirements.md`、`docs/detail_design.md`、`docs/trace_map.md`）と実装の整合を逆引きで確かめ、未マッピング一覧と要件ごとの実装済み判定を報告に出す。
8.5 `check.sh --strict`、単体・E2E テストを全件通るまで最後にもう一度実行する。

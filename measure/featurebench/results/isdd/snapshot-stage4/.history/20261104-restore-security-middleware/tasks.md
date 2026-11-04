# 実装タスク（Flask セキュリティミドルウェアの復元：mlflow/server/security.py と mlflow/server/security_utils.py）

前提: `docs/active_change` が本変更（`.history/20261104-restore-security-middleware/`）を指している。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装中に書き換えない（反映は実装後レビュー）。
対象の変更設計 ID: `DS-MD-SERVER-SECURITY-MODULE`、`DS-MD-SERVER-SECURITY-UTILS-MODULE`、`DS-FN-GET-ALLOWED-HOSTS`、`DS-FN-GET-ALLOWED-ORIGINS`、`DS-FN-INIT-SECURITY-MIDDLEWARE`、`DS-FN-IS-ALLOWED-HOST-HEADER`、`DS-FN-GET-ALLOWED-HOSTS-FROM-ENV`、`DS-FN-GET-ALLOWED-ORIGINS-FROM-ENV`、`DS-FN-GET-LOCALHOST-ADDRESSES`、`DS-FN-GET-PRIVATE-IP-PATTERNS`、`DS-FN-GET-DEFAULT-ALLOWED-HOSTS`、`DS-FN-IS-API-ENDPOINT`、`DS-FN-IS-LOCALHOST-ORIGIN`、`DS-FN-SHOULD-BLOCK-CORS-REQUEST`、`DS-TS-SECURITY-*`（5 件）。

## タスク

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` などが存在する。`scripts/isdd/completeness.json` の実行形態（cli）・認証（無し）・外部連携（無し）が、正本の詳細設計書と一致していることを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` が実行できること。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-restore-security-middleware` を指していることを確認する。正本には変更を反映しない。
   - `scripts/isdd/check.sh` の 3 つの呼び出しに `mlflow/server` が入っていることを確認する（本変更で追加済み）。
   - 完了条件: `python3 /Users/notfolder/.claude/skills/isdd-spec/scripts/rq_ds_link_checker.py .history/20261104-restore-security-middleware/change_requirements.md .history/20261104-restore-security-middleware/change_detail_design.md --base docs/requirements.md` が合格すること。

1. **共通部品の復元**（`DS-FN-IS-ALLOWED-HOST-HEADER`、`DS-FN-GET-ALLOWED-HOSTS-FROM-ENV`、`DS-FN-GET-ALLOWED-ORIGINS-FROM-ENV`、`DS-FN-GET-LOCALHOST-ADDRESSES`、`DS-FN-GET-PRIVATE-IP-PATTERNS`、`DS-FN-GET-DEFAULT-ALLOWED-HOSTS`、`DS-FN-IS-API-ENDPOINT`、`DS-MD-SERVER-SECURITY-UTILS-MODULE`）
   - `mlflow/server/security_utils.py` に、`is_allowed_host_header(allowed_hosts: list[str], host: str) -> bool` と、設計書 4-2 の補助関数を書く。`security.py` と `fastapi_security.py` が import している名前がすべて解決するようにする。
   - 既存の定数、`is_localhost_origin`、`should_block_cors_request` は変えない。
   - 完了条件: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -c "from mlflow.server.security_utils import is_allowed_host_header, get_default_allowed_hosts, is_api_endpoint"'` がエラーなく終わること。

2. **Flask 向けの安全策の復元**（`DS-FN-GET-ALLOWED-HOSTS`、`DS-FN-GET-ALLOWED-ORIGINS`、`DS-FN-INIT-SECURITY-MIDDLEWARE`、`DS-MD-SERVER-SECURITY-MODULE`）
   - `mlflow/server/security.py` の `get_allowed_hosts`、`get_allowed_origins`、`init_security_middleware(app: Flask) -> None` を書く。引数名・戻り値の型は依頼文の Interface Description どおり。既存の import 行は変えない（必要な名前は既に import されている）。
   - 設計書 4-2 の順序（無効化の判定、CORS、Host 検査、CORS 遮断、応答ヘッダー）に従う。
   - 完了条件: `init_security_middleware` が `MLFLOW_SERVER_DISABLE_SECURITY_MIDDLEWARE=true` で何もせず、他では設計書どおりに動くこと（タスク 4 の E2E で確かめる）。

3. **E2E テストの実装**（`DS-TS-SECURITY-ALLOWED-HOSTS-AND-ORIGINS`、`DS-TS-SECURITY-HOST-VALIDATION`、`DS-TS-SECURITY-CORS-BLOCKING`、`DS-TS-SECURITY-RESPONSE-HEADERS`、`DS-TS-SECURITY-DISABLED`）
   - `e2e/test_security_middleware.py` を新規に作る。公開インターフェースと Flask のテストクライアントだけを使い、設計書 8-2 の 5 シナリオを、それぞれ 1 つのテスト関数に書く（関数名は DS-TS の名前を小文字・アンダースコアにした形、例 `test_security_host_validation`）。環境変数は monkeypatch で設定する。
   - 既存の `e2e/test_claude_code.py`、`e2e/test_trace_correlation.py` は変えない。
   - 完了条件: タスク 5 の実行で、対応する 5 関数が通ること。

4. **対応表（docs/trace_map.md）更新タスク**
   - 変更設計書 5-4 の 11 個の関数（`DS-FN-*`）、7-2 の 2 ファイル（`DS-MD-*`）、8-2 の 5 シナリオ（`DS-TS-*`）の行を足す。書式は trace-map-rules.md（修飾名は `mlflow/server/security.py::init_security_middleware` の形。`DS-MD` はファイルパス、`DS-TS` は `e2e/test_security_middleware.py::test_...` の形）。
   - 完了条件: `bash scripts/isdd/check.sh` の対応表チェックで、今回の変更の項目が未登録になっていないこと。

5. **E2E テスト全件通過タスク**
   - 実行コマンド（設計書 8-4）: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml'`
   - 完了条件: 本変更の 5 関数に FAIL が 0 件。既存の E2E（`test_claude_code.py`、`test_trace_correlation.py`）にも FAIL が無いこと。

6. **既存の単体テスト確認タスク**
   - 既存のテストのうち安全策に触れるもの（`tests/server/` の security 関連）を実行し、FAIL が無いことを確かめる: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest tests/server -k "security or host or cors"'`。該当が無ければ「テスト無し」と報告する。
   - 完了条件: 実行したテストに FAIL が 0 件（既存の失敗は報告に書く）。

7. **変更の全件確認タスク**（変更要件・変更設計書の全項目を実装したかの確認）
   - 変更設計書 5-4 の関数、7-2 の 2 ファイル、8-2 の 5 シナリオ、11 章の全設計 ID に対応する実装とテストがあることを確かめる。
   - 完了条件: 漏れが無いこと。

8. **実装完了チェックタスク**
   - `bash scripts/isdd/check.sh` を実行する。`--strict` は、`mlflow/server/` の他のファイル（本変更の対象外）の未登録の関数で失敗する見込みのため、結果を報告に書く（対応は実装後レビューの判断に従う）。
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。完了条件: 全項目が OK（対象外の項目は理由を報告に書く）。

9. **起動確認タスク**: 対象外（理由: ライブラリの関数で、詳細設計書 9-1 に起動方法が無い。Flask への登録は E2E で確かめる）。

10. **README.md 記載タスク**: 対象外（理由: 既存の README と `mlflow/server/AGENTS.md` を変えない）。

## 修正が要る場合の扱い

- 実装中に設計に無い設計要素が要ることが分かったら、実装を止めて `isdd-spec` での見直しに戻す（設計 ID を実装中に作らない）。

## 依頼の範囲外の既存の不具合

- 依頼の範囲外の既存の不具合は直さず、正本に現状として書く（報告に含める）。
- 既存の `mlflow/server/fastapi_security.py` は、本変更で補助関数が戻るまで import が解決しなかった。解決後の挙動は既存のままで、変更していない（報告に含める）。

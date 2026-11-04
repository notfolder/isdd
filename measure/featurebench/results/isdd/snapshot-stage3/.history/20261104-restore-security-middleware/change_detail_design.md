# 変更設計書（Flask セキュリティミドルウェアの復元：mlflow/server/security.py と mlflow/server/security_utils.py）

正本: `docs/detail_design.md`（`mlflow/claude_code/` と `mlflow/store/analytics/` の逆引き）。本書は正本を書き換えない。区分は [追加] のみ。
変更要件: `change_requirements.md`。本変更は新しい範囲 `mlflow/server/` を正本に足す（実装後レビューで正本へ反映する）。

## 1. 言語・フレームワーク・アーキテクチャの選定

既存コードベースの選定を使う。Python、Flask、Flask-CORS（既存の依存）、既存の環境変数の定義（`mlflow/environment_variables.py`）。新しい依存は足さない。DB は使わない。実行形態は Flask アプリへのミドルウェア登録（サーバー起動時）。

| 項目 | 選定 | 根拠 |
|---|---|---|
| 言語 | Python | 既存コードの言語 |
| Web フレームワーク | Flask（`flask.Response`、`request`、`before_request`、`after_request`） | `security.py` の既存 import と、サーバーの既存の Flask アプリ |
| CORS | Flask-CORS（`CORS(app, resources=..., supports_credentials=True, methods=...)`） | `security.py` の既存 import |
| 環境変数 | `mlflow/environment_variables.py` の既存の定義 | `security_utils.py` と `security.py` の既存 import |
| DB 製品 | 無し | 要件定義書 4-1 |
| 実行形態 | Flask アプリへの登録（ライブラリ内） | 変更要件定義書 1-2 |
| 承認 | 固定回答（ANSWERS.md）と依頼文により承認済み | ANSWERS.md、REQUEST.md |

## 2. システム構成

### 2-1. コンポーネント一覧

| コンポーネント | 役割 | 配置 |
|---|---|---|
| Flask 向けの安全策モジュール | 許可設定の読み出し、Flask へのミドルウェア登録 | `mlflow/server/security.py` |
| 安全策の共通部品 | 定数、環境変数の読み出し、Host・CORS の判定の補助 | `mlflow/server/security_utils.py` |

### 2-2. 各コンポーネントの役割と機能

- 安全策モジュールは、許可ホスト（`get_allowed_hosts`）と許可オリジン（`get_allowed_origins`）を取り出し、`init_security_middleware` で Flask アプリに CORS・Host 検査・CORS 遮断・応答ヘッダーを登録する。
- 共通部品は、環境変数の値をリストにする関数、既定の許可ホストを作る関数、Host ヘッダーを照合する関数、API 経路の判定、CORS 遮断の判定を持つ。

### 2-3. コンポーネント間インターフェースとデータフロー

- 入力: 環境変数（`MLFLOW_SERVER_ALLOWED_HOSTS`、`MLFLOW_SERVER_CORS_ALLOWED_ORIGINS`、`MLFLOW_SERVER_X_FRAME_OPTIONS`、`MLFLOW_SERVER_DISABLE_SECURITY_MIDDLEWARE`）、Flask のリクエスト（Host、Origin、メソッド、経路）。
- 出力: Flask の応答（403 の本文、または通常の応答に付けたヘッダーと状態）。関数の戻り値は依頼文の Interface Description どおり。
- 呼び出し元: `mlflow/server/__init__.py` が `security.init_security_middleware(app)` を呼ぶ（既存）。`mlflow/server/fastapi_security.py` が `security_utils.py` の補助関数を import する（既存。本変更で解決する）。

### 2-4. ネットワーク構成図

無し（ライブラリ内の処理）。

## 3. データ設計

### 3-1. データモデル

無し（新しいデータ型は作らない）。既存の定数を使う。`security_utils.py` の定数: `INVALID_HOST_MSG`、`CORS_BLOCKED_MSG`、`STATE_CHANGING_METHODS`、`HEALTH_ENDPOINTS`、`API_PATH_PREFIX`、`TEST_ENDPOINTS`、`LOCALHOST_VARIANTS`、`CORS_LOCALHOST_HOSTS`、`PRIVATE_172_RANGE_START`、`PRIVATE_172_RANGE_END`、`LOCALHOST_ORIGIN_PATTERNS`。

### 3-2. トランザクションと排他制御

無し。

### 3-3. 状態遷移

無し。

## 4. アーキテクチャ設計

### 4-1. 外部設計

利用者（開発者・運用者）向けの入口は次のとおり（依頼文の Interface Description どおりの引数と戻り値）。

- `mlflow.server.security.get_allowed_hosts() -> list[str]`
- `mlflow.server.security.get_allowed_origins() -> list[str]`
- `mlflow.server.security.init_security_middleware(app) -> None`（`app` は Flask）
- `mlflow.server.security_utils.is_allowed_host_header(allowed_hosts, host) -> bool`

### 4-2. 内部設計

`security.py` の関数:

- `get_allowed_hosts()` は `get_allowed_hosts_from_env() or get_default_allowed_hosts()`。
- `get_allowed_origins()` は `get_allowed_origins_from_env() or []`。
- `init_security_middleware(app)` は次の順で処理する。
  1. `MLFLOW_SERVER_DISABLE_SECURITY_MIDDLEWARE.get() == "true"` なら何もせず戻る。
  2. 許可オリジンと許可ホストを取得し、X-Frame-Options の設定値を読む。
  3. CORS: 許可オリジンに `*` があれば `CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)`。無ければ `(許可オリジン + LOCALHOST_ORIGIN_PATTERNS)` を origins にして、`methods=["GET","POST","PUT","DELETE","OPTIONS","PATCH"]` と `supports_credentials=True` を付けて `CORS` を呼ぶ。
  4. 許可ホストが空でなく `*` を含まなければ、`before_request` で Host 検査を登録する。`request.path` が `HEALTH_ENDPOINTS` に入るなら通す。違えば `is_allowed_host_header` で照合し、不合格なら `INVALID_HOST_MSG` を 403（text/plain）で返す。
  5. 許可オリジンに `*` が無ければ、`before_request` で CORS 遮断を登録する。`is_api_endpoint(request.path)` が偽なら通す。真なら `should_block_cors_request(origin, method, allowed_origins)` で判定し、真なら `CORS_BLOCKED_MSG` を 403（text/plain）で返す。
  6. `after_request` で応答ヘッダーを付ける。`X-Content-Type-Options: nosniff` は常に付ける。`X-Frame-Options` は設定値が空でなく大文字化して `NONE` でなく、経路が `TRACE_RENDERER_ASSET_PATH` で始まらないときだけ、設定値を大文字にして付ける。OPTIONS かつ API 経路かつ状態 200 のときは状態を 204 にし、本文を空にする。

`security_utils.py` の関数（`is_allowed_host_header` と、それが使う既存の import 先の補助）:

- `is_allowed_host_header(allowed_hosts, host)`: `host` が空や None なら False。`allowed_hosts` に `*` があれば True。それ以外は、各パターンについて `*` を含むなら `fnmatch.fnmatch(host, pattern)`、含まないなら `host == pattern`。いずれかに合えば True。
- `get_allowed_hosts_from_env()`: `MLFLOW_SERVER_ALLOWED_HOSTS.get()` が真なら、カンマで分けて各要素の前後の空白を除いたリスト。無ければ None。
- `get_allowed_origins_from_env()`: `MLFLOW_SERVER_CORS_ALLOWED_ORIGINS.get()` について同じ規則。
- `get_localhost_addresses()`: `LOCALHOST_VARIANTS` を返す。
- `get_private_ip_patterns()`: `192.168.*`、`10.*`、`172.16.*`〜`172.31.*`（`PRIVATE_172_RANGE_START` 以上 `PRIVATE_172_RANGE_END` 未満）、`fc00:*`、`fd00:*` のリスト。
- `get_default_allowed_hosts()`: localhost 系の各アドレス（そのまま）、各アドレスの `:*` 付き（`[::1]` は `[[]::1]:*` のように開き括弧をエスケープする）、そして `get_private_ip_patterns()` を連結して返す。
- `is_api_endpoint(path)`: `path` が `API_PATH_PREFIX`（`/api/`）で始まり、かつ `TEST_ENDPOINTS` に無いなら True。
- 既存の `is_localhost_origin(origin)` と `should_block_cors_request(origin, method, allowed_origins)` は変えない（既存の挙動を保つ）。

既存の `LOCALHOST_ORIGIN_PATTERNS` は `security.py` が CORS の origins に使う（既存の定数）。

### 4-3. バッチ設計

無し。

## 5. クラス設計

### 5-1. クラス一覧

本変更で新しいクラスは作らない（既存のクラスも無い）。

### 5-2. クラスの責務・属性

該当なし。

### 5-3. クラス図

無し（クラスを持たない）。

### 5-4. 関数の責務

| 区分 | DS-ID | 関数 | 責務（1 文） |
|---|---|---|---|
| [追加] | `DS-FN-GET-ALLOWED-HOSTS` | `get_allowed_hosts` | 環境変数の許可ホストを優先し、無ければ既定の許可ホストを返す |
| [追加] | `DS-FN-GET-ALLOWED-ORIGINS` | `get_allowed_origins` | 環境変数の許可オリジンを返し、無ければ空のリストを返す |
| [追加] | `DS-FN-INIT-SECURITY-MIDDLEWARE` | `init_security_middleware` | 無効化の判定の後、Flask に CORS・Host 検査・CORS 遮断・応答ヘッダーを登録する |
| [追加] | `DS-FN-IS-ALLOWED-HOST-HEADER` | `is_allowed_host_header` | Host の値が許可パターンのどれかに合うかを判定する |
| [追加] | `DS-FN-GET-ALLOWED-HOSTS-FROM-ENV` | `get_allowed_hosts_from_env` | 環境変数の許可ホストをカンマで分けたリストにする（無い場合は None） |
| [追加] | `DS-FN-GET-ALLOWED-ORIGINS-FROM-ENV` | `get_allowed_origins_from_env` | 環境変数の許可オリジンをカンマで分けたリストにする（無い場合は None） |
| [追加] | `DS-FN-GET-LOCALHOST-ADDRESSES` | `get_localhost_addresses` | localhost 系のアドレスの一覧を返す |
| [追加] | `DS-FN-GET-PRIVATE-IP-PATTERNS` | `get_private_ip_patterns` | プライベートアドレス範囲の fnmatch パターンを返す |
| [追加] | `DS-FN-GET-DEFAULT-ALLOWED-HOSTS` | `get_default_allowed_hosts` | 既定の許可ホスト（localhost とポート付き、プライベート範囲）を返す |
| [追加] | `DS-FN-IS-API-ENDPOINT` | `is_api_endpoint` | 経路が API 経路（テスト専用を除く）かを判定する |
| [追加] | `DS-FN-IS-LOCALHOST-ORIGIN` | `is_localhost_origin` | オリジンが localhost かを判定する（変更なし） |
| [追加] | `DS-FN-SHOULD-BLOCK-CORS-REQUEST` | `should_block_cors_request` | 状態を変える要求で、許可されていないオリジンを遮断するかを判定する（変更なし） |

詳細規則（`init_security_middleware` の順序と分岐）は 4-2 のとおり。

### 5-5. クラス図とメッセージ

無し。

## 6. エラーハンドリングとセキュリティ設計

### 6-1. エラーハンドリング

- 不正な Host: 403（本文 `INVALID_HOST_MSG`、text/plain）。例外は投げない。
- 遮断された CORS 要求: 403（本文 `CORS_BLOCKED_MSG`、text/plain）。
- 空の Host や不正な値は、照合で False（例外にしない）。
- `is_localhost_origin` は例外を握りつぶして False を返す（既存の挙動）。

### 6-2. 認証・認可・監査ログ

認証・認可は対象外（要件定義書 1-0）。拒否した要求は `_logger.warning` で記録する（既存の記録）。

### 6-3. その他のセキュリティ対策

本変更の対策は、Host 検査、CORS 遮断、応答ヘッダー（要件定義書 1-0 の 3 つ）に限る。

## 7. コード設計

### 7-1. ディレクトリ構成

```
mlflow/server/
  security.py         （Flask 向けの許可設定の読み出しと、ミドルウェアの登録）
  security_utils.py   （安全策の共通部品）
  fastapi_security.py （既存。本変更では変えない）
  （その他の既存ファイル。本変更では変えない）
```

本変更で書き換えるのは `security.py` と `security_utils.py` の 2 ファイルだけ。既存の `fastapi_security.py` の import が解決するように、`security_utils.py` に補助関数を戻す。

### 7-2. ファイルごとの役割

| 区分 | ファイル | 役割 | 含まれるクラス・公開関数 | 実現する設計 ID |
|---|---|---|---|---|
| [追加] | `mlflow/server/security.py` | Flask の許可設定の読み出しと、ミドルウェアの登録 | `get_allowed_hosts`、`get_allowed_origins`、`init_security_middleware` | `DS-MD-SERVER-SECURITY-MODULE`、`DS-FN-GET-ALLOWED-HOSTS`、`DS-FN-GET-ALLOWED-ORIGINS`、`DS-FN-INIT-SECURITY-MIDDLEWARE` |
| [追加] | `mlflow/server/security_utils.py` | 安全策の共通部品（環境変数の読み出し、既定のホスト、照合、API 経路の判定） | `is_allowed_host_header`、`get_allowed_hosts_from_env`、`get_allowed_origins_from_env`、`get_localhost_addresses`、`get_private_ip_patterns`、`get_default_allowed_hosts`、`is_api_endpoint`、`is_localhost_origin`、`should_block_cors_request` | `DS-MD-SERVER-SECURITY-UTILS-MODULE`、`DS-FN-IS-ALLOWED-HOST-HEADER`、`DS-FN-GET-ALLOWED-HOSTS-FROM-ENV`、`DS-FN-GET-ALLOWED-ORIGINS-FROM-ENV`、`DS-FN-GET-LOCALHOST-ADDRESSES`、`DS-FN-GET-PRIVATE-IP-PATTERNS`、`DS-FN-GET-DEFAULT-ALLOWED-HOSTS`、`DS-FN-IS-API-ENDPOINT`、`DS-FN-IS-LOCALHOST-ORIGIN`、`DS-FN-SHOULD-BLOCK-CORS-REQUEST` |

対応表の粒度: `function`。依存の規則: 無い（`mlflow/server/` 内の import の制約は設けない）。

### 7-3. 対応表の粒度

`function`（公開関数まで対応表に載せる）。

### 7-4. 依存の規則

無い。

### 7-5. コーディング規約

- Python の既存の規約（リポジトリの pyproject と ruff の設定）に従う。
- 関数の docstring は依頼文の Interface Description を使う。
- コードに要件 ID と設計 ID は書かない。

## 8. テスト設計

### 8-1. テストの種類と方針

- 単体テスト: 既存の mlflow の tests/ は変更しない。依頼の隠しテストが単体テストを担うため、本変更では単体テストを追加しない。
- 総合テスト・E2E: 本書 8-2 のシナリオを `e2e/test_security_middleware.py` で実行する（公開インターフェース `init_security_middleware`、`get_allowed_hosts`、`get_allowed_origins`、`is_allowed_host_header` と Flask のテストクライアントだけを使う）。

### 8-2. E2E テストのシナリオ

| 区分 | DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| [追加] | `DS-TS-SECURITY-ALLOWED-HOSTS-AND-ORIGINS` | 許可ホストと許可オリジンが環境変数の有無で切り替わる | 環境変数の未設定・設定・空文字（monkeypatch） | 2 つの関数を呼ぶ | 未設定・空文字では既定のホスト一覧と空のオリジン。設定時はカンマ区切りの値（空白を除く） |
| [追加] | `DS-TS-SECURITY-HOST-VALIDATION` | 不正な Host は 403、健康確認と許可された Host は通る。照合の規則 | Flask アプリに安全策を登録（既定の許可ホスト） | 不正な Host・許可された Host で GET し、`/health` を GET する。`is_allowed_host_header` を各規則で呼ぶ | 不正な Host は 403、許可された Host と `/health` は通る。`*` は全許可、空は False、完全一致と fnmatch は仕様どおり |
| [追加] | `DS-TS-SECURITY-CORS-BLOCKING` | 別オリジンからの API の状態変更要求は 403、localhost と許可オリジンは通る | 許可オリジンは既定（空）と指定（`https://app.example.com`）の 2 通り | 別オリジンから `/api/` に POST、localhost と許可オリジンからも POST | 別オリジンは 403、localhost と許可オリジンは通る |
| [追加] | `DS-TS-SECURITY-RESPONSE-HEADERS` | 応答ヘッダーの付与と、OPTIONS の 204 | 既定の X-Frame-Options（SAMEORIGIN）と NONE の 2 通り | 通常経路、ノートブックの経路、API の OPTIONS を呼ぶ | nosniff は常に付く。X-Frame-Options は SAMEORIGIN（ノートブックと NONE では付かない）。API の OPTIONS の 200 は 204 |
| [追加] | `DS-TS-SECURITY-DISABLED` | 無効化は厳密に `"true"` のときだけ | 環境変数を `true`・`TRUE`・未設定にする | 安全策を登録し、不正な Host で GET する | `true` では不正な Host でも通る。`TRUE`・未設定では 403 |

### 8-3. E2E の実行手段

pytest（コンテナ内の Python）。Flask のテストクライアントを使う。

### 8-4. E2E の実行コマンドと運用

- 実行コマンド: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml'`
- 結果: `e2e/results/e2e.xml`。
- 外部連携は無いため、モックのモードは設けない。
- 実装時の必須ゴールは E2E の全件通過。

## 9. 運用設計

### 9-1. 起動・インストール

無し（mlflow サーバーの既存の起動経路で呼ばれる）。

### 9-2. バックアップと復旧

無し。

### 9-3. データ移行

無し。

### 9-4. 可用性

無し。

## 10. ログ・監視・アラート・障害対応設計

拒否した要求は既存の `_logger.warning` で記録する（不正な Host、遮断された CORS 要求）。追加の監視は無い。

## 11. 要件と設計の対応表

| 区分 | DS-ID | 対応要件ID |
|---|---|---|
| [追加] | `DS-MD-SERVER-SECURITY-MODULE` | `RQ-FT-GET-ALLOWED-HOSTS`, `RQ-FT-GET-ALLOWED-ORIGINS`, `RQ-FT-INIT-SECURITY-MIDDLEWARE` |
| [追加] | `DS-MD-SERVER-SECURITY-UTILS-MODULE` | `RQ-FT-IS-ALLOWED-HOST-HEADER`, `RQ-FT-GET-ALLOWED-HOSTS`, `RQ-FT-GET-ALLOWED-ORIGINS`, `RQ-FT-INIT-SECURITY-MIDDLEWARE` |
| [追加] | `DS-FN-GET-ALLOWED-HOSTS` | `RQ-FT-GET-ALLOWED-HOSTS` |
| [追加] | `DS-FN-GET-ALLOWED-ORIGINS` | `RQ-FT-GET-ALLOWED-ORIGINS` |
| [追加] | `DS-FN-INIT-SECURITY-MIDDLEWARE` | `RQ-FT-INIT-SECURITY-MIDDLEWARE` |
| [追加] | `DS-FN-IS-ALLOWED-HOST-HEADER` | `RQ-FT-IS-ALLOWED-HOST-HEADER` |
| [追加] | `DS-FN-GET-ALLOWED-HOSTS-FROM-ENV` | `RQ-FT-GET-ALLOWED-HOSTS` |
| [追加] | `DS-FN-GET-ALLOWED-ORIGINS-FROM-ENV` | `RQ-FT-GET-ALLOWED-ORIGINS` |
| [追加] | `DS-FN-GET-LOCALHOST-ADDRESSES` | `RQ-FT-GET-ALLOWED-HOSTS` |
| [追加] | `DS-FN-GET-PRIVATE-IP-PATTERNS` | `RQ-FT-GET-ALLOWED-HOSTS` |
| [追加] | `DS-FN-GET-DEFAULT-ALLOWED-HOSTS` | `RQ-FT-GET-ALLOWED-HOSTS` |
| [追加] | `DS-FN-IS-API-ENDPOINT` | `RQ-FT-INIT-SECURITY-MIDDLEWARE` |
| [追加] | `DS-FN-IS-LOCALHOST-ORIGIN` | `RQ-FT-INIT-SECURITY-MIDDLEWARE` |
| [追加] | `DS-FN-SHOULD-BLOCK-CORS-REQUEST` | `RQ-FT-INIT-SECURITY-MIDDLEWARE` |
| [追加] | `DS-TS-SECURITY-ALLOWED-HOSTS-AND-ORIGINS` | `RQ-TS-SECURITY-ALLOWED-HOSTS-AND-ORIGINS` |
| [追加] | `DS-TS-SECURITY-HOST-VALIDATION` | `RQ-TS-SECURITY-HOST-VALIDATION` |
| [追加] | `DS-TS-SECURITY-CORS-BLOCKING` | `RQ-TS-SECURITY-CORS-BLOCKING` |
| [追加] | `DS-TS-SECURITY-RESPONSE-HEADERS` | `RQ-TS-SECURITY-RESPONSE-HEADERS` |
| [追加] | `DS-TS-SECURITY-DISABLED` | `RQ-TS-SECURITY-DISABLED` |

### 11-1. 除外要件

除外要件は無い。

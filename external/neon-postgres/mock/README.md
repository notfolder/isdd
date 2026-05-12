# psycopgモック利用手順

## 1. 目的

- 外部Neon PostgreSQLへ接続せず、部署名取得ロジックを検証する。
- `user_id` に応じて部署名を返し、未存在ユーザーは `None` を返す。

## 2. 実装内容

- ファイル: `external/neon-postgres/mock/psycopg_mock.py`
- 提供機能:
  - `connect`: `psycopg.connect` 互換のモック接続
  - `patch_psycopg_connect`: `psycopg.connect` 差し替え用patch
  - SQL簡易解析: `WHERE user_id = %s` / `%(user_id)s` / リテラル `'U001'` を抽出
  - 返却仕様:
    - 既知ユーザー: 部署名（例: `営業部`）
    - 未知ユーザー: `None`

## 3. 想定クエリ

- `public.demo_users` を参照し、`department_name` を取得するSELECT
- JOINを含むクエリを含め、`department_name` をSELECTしていれば `None` 含め返却可能

## 4. 運用ルール

- mockモードのE2Eでは `patch_psycopg_connect` を利用して外部接続を置き換える。
- realモードではpatchを適用せず実DBを参照する。
- モックデータの主キーは `user_id` とし、既存Neonサンプル（`U001` 〜 `U010`）と整合させる。

## 5. 実行モード切替

- バックエンドから `department_reader.py` を利用する場合は以下の環境変数で切り替える。
  - mockモード: `EXTERNAL_DEPARTMENT_DB_USE_MOCK=1`
  - realモード: `EXTERNAL_DEPARTMENT_DB_URL=<Neon接続文字列>`
- mockモードでは `external/neon-postgres/mock/psycopg_mock.py` の `connect` を直接利用する。

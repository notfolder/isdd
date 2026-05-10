# 外部連携 事前確認レポート（precheck）

## 1. 連携先概要

- 連携先システム名: Neon PostgreSQL（管理上識別名: `neon-postgres`）
- 連携目的: 外部DBから部署名を取得し、アプリ内の業務表示に利用する
- 連携対象（確認済み）:
  - `public.demo_departments`（`department_id`, `department_name`）
  - `public.demo_users`（`user_id`, `user_name`, `department_id`）
- 接続方式: PostgreSQL接続文字列（TLS必須）

## 2. 接続可否判定

- 判定: **接続可能**
- 実施内容:
  - Python仮想環境（`./.venv`）を作成
  - `psycopg` を導入して接続テストを実施
  - DB接続、テーブル一覧取得、カラム一覧取得、サンプル参照まで成功
- 接続経路・認可手続きの制約: **制約なし**（ユーザー回答）

## 3. 認証方式

- 認証方式: **ID/パスワード認証 + TLS**
- 暗号化要件: `sslmode=require` 前提
- アプリ側で管理する環境変数名:
  - `EXTERNAL_DEPARTMENT_DB_URL`（外部DB接続文字列）
- 記録方針: 認証情報の実値はドキュメントに記載しない

## 4. 主要制限

- 契約・利用時間帯・レートに関する制限: **なし**（ユーザー回答）
- 運用上の利用制約: アプリからの外部DB操作は **読み取り専用**（ユーザー回答）
- 補足（接続確認時に観測した設定）:
  - `statement_timeout=0`
  - `lock_timeout=0`
  - `idle_in_transaction_session_timeout=5min`

## 5. 後続 isdd-external-research の調査対象範囲

- 外部DBスキーマ整合の詳細確認
  - 部署名取得の正規参照元テーブルを `public.demo_departments` として確定
  - `department_id` の参照整合と欠損時挙動を要件へ反映
- 予約機能との整合確認
  - 予約対象エンティティ（備品）との結合条件
  - 一覧表示・詳細表示での部署名表示要否
- 非機能制約の整合
  - 外部DB参照時の応答性能要件
  - 接続失敗時のエラー扱い（再試行有無、業務継続条件）

## 6. 要件定義に進んで良いかの判定

- 判定: **進行可**
- 要件定義へ引き継ぐ制約事項:
  - 外部連携は Neon PostgreSQL を利用する
  - 認証は ID/パスワード + TLS を採用する
  - 接続経路制約・主要制限はなし
  - アプリからの操作は読み取り専用に限定する

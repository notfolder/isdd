# 備品管理・貸出管理アプリ

備品の登録・管理と利用者への貸出・返却を行うWebアプリケーションです。

## 技術スタック

- **フロントエンド**: Vue 3 + Vuetify 3 + Pinia + Vue Router
- **バックエンド**: Python + FastAPI + SQLAlchemy + SQLite
- **認証**: JWT（HTTP-only Cookie、60分セッション）
- **E2Eテスト**: Playwright v1.59.0

## セットアップ

### 1. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成します。

```bash
cp .env.example .env
```

`.env` ファイルを編集して本番用の値を設定してください。

```env
INITIAL_ADMIN_LOGIN_ID=admin
INITIAL_ADMIN_PASSWORD=changeme
JWT_SECRET_KEY=change-this-secret-key-in-production
```

| 変数名 | 説明 | デフォルト値 |
|---|---|---|
| `INITIAL_ADMIN_LOGIN_ID` | 初期管理者のログインID | `admin` |
| `INITIAL_ADMIN_PASSWORD` | 初期管理者のパスワード | `changeme` |
| `JWT_SECRET_KEY` | JWT署名用秘密鍵 | `change-this-secret-key-in-production` |

> **注意**: 本番環境では必ず `JWT_SECRET_KEY` を強固な値に変更してください。

### 2. アプリケーションの起動

```bash
docker compose up -d
```

起動後、ブラウザで http://localhost にアクセスしてください。

### 3. アプリケーションの停止

```bash
docker compose down
```

DBデータも含めて完全削除する場合:

```bash
docker compose down -v
```

## E2Eテストの実行

アプリケーションを起動した状態でE2Eテストを実行します。

```bash
docker compose --profile test run --rm test_playwright npx playwright test
```

テスト結果の詳細を表示する場合:

```bash
docker compose --profile test run --rm test_playwright npx playwright test --reporter=list
```

## 機能一覧

### 管理者

- **備品管理**: 備品の登録・編集・削除
- **貸出管理**: 備品の貸出・返却
- **利用者管理**: 利用者の登録・編集・削除

### 一般利用者

- **備品閲覧**: 全備品と貸出状態の確認（操作不可）

## 仕様書

- [要件定義書](docs/requirements.md)
- [詳細設計書](docs/detail_design.md)

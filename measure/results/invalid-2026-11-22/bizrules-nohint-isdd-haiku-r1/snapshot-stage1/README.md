# 備品の貸出管理

会社の備品の貸出を管理する Web アプリ。社員は貸出状況を誰でも見られ、担当者は備品の登録と貸出・返却を記録する。社内のサーバーで動かし、社内のネットワークからだけ開く。

## 起動方法

Python 3.12 が必要。

1. 初回の準備（1 回だけ）: `bash setup.sh`
   仮想環境を作り、依存を入れ、E2E テスト用の Chromium を取得する。
2. 起動: `bash run.sh`
   既定ではポート 8000 で待ち受ける。ブラウザで `http://localhost:8000/` を開く。

### 環境変数

| 名前 | 用途 | 既定値 |
|---|---|---|
| `PORT` | 待ち受けポート | 8000 |
| `DATA_DIR` | DB（`lending.sqlite3`）と秘密鍵（`secret_key`）の置き場所 | プロジェクト直下の `data/` |
| `DJANGO_SECRET_KEY` | Django の秘密鍵。省略時は `DATA_DIR/secret_key` を自動で作る | 省略可 |
| `ALLOWED_HOSTS` | 受け付けるホスト名（カンマ区切り） | `localhost,127.0.0.1` |

### 初期ユーザー

初期ユーザーは無い。最初に登録したアカウントが担当者になり、2 件目以降は社員になる。アカウント登録は `/accounts/register/` から行う。

### 操作の流れ

- 社員番号 6 桁、名前 30 文字以内、パスワード 8 文字以上でアカウントを登録する。
- 担当者は「備品を登録」から備品を登録し、行の「貸出」で借りる社員と貸出日を選ぶ。「返却」で貸出の記録を消して空きに戻す。

## テスト

- 単体・結合テスト: `.venv/bin/python -m pytest tests -q`
- E2E テスト: `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`（`run.sh` を一時のデータで起動して操作する）

## 設計資料

- 要件定義書: `docs/requirements.md`
- 詳細設計書: `docs/detail_design.md`
- 対応表: `docs/trace_map.md`

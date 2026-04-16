# シグマプロット比較アプリ

CSV ファイルから 2 カラムのデータを指定し、Q-Q プロットとヒストグラムで 2 つの分布を比較する Web アプリケーション。

## 機能一覧

- **ファイル選択**: CSV ファイルのアップロード
- **カラム選択**: 2 つのカラムを選択して比較対象を指定
- **Q-Q プロット表示**: 2 つの分布の Q-Q プロットを表示
- **ヒストグラム併記**: ヒストグラムを重ねて表示するオプション
- **プロット保存**: 描画されたプロットを PNG 形式で保存

## システム要件

- Python 3.10+
- Docker & Docker Compose
- Streamlit
- matplotlib, numpy

## インストールと起動

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. Docker コンテナの起動

```bash
docker compose up -d
```

### 3. アプリケーションへのアクセス

ブラウザで以下の URL にアクセスします：

- **Streamlit アプリ**: http://localhost:8501
- **E2E テスト**: `docker compose --profile test up test_playwright`

## 使用方法

### Step 1: ファイルを選択
- CSV ファイルを選択してアップロードします
- ファイルサイズは 10MB 以内です

### Step 2: カラムを選択
- CSV ファイル内のカラム一覧が表示されます
- 比較したい 2 つのカラムを選択します

### Step 3: Q-Q プロットを表示
- Q-Q プロットが表示されます
- ヒストグラムを表示するチェックボックスで併記できます

### Step 4: プロットを保存（オプション）
- 保存パスを入力してプロットを PNG 形式で保存できます

## プロジェクト構造

```
sigma_plot_app/
├── app.py                    # Streamlit アプリケーションのエントリーポイント
├── services/
│   ├── __init__.py
│   ├── file_service.py       # ファイル処理サービス
│   ├── column_service.py     # カラム管理サービス
│   └── plot_service.py       # プロット生成サービス
├── utils/
│   ├── __init__.py
│   ├── validation.py         # 検証ユーティリティ
│   └── error_handler.py      # エラーハンドリングユーティリティ
├── tests/
│   ├── __init__.py
│   └── test_services.py      # サービステスト
├── e2e/                      # E2E テスト
│   └── test_e2e.py
├── Dockerfile                # Streamlit コンテナ用
├── docker-compose.yml        # コンテナオーケストレーション
└── requirements.txt          # Python 依存パッケージ
```

## エラーハンドリング

| エラータイプ | 発生条件 | 対応措置 |
|-------------|---------|----------|
| `FileNotFoundError` | CSV ファイルが指定されたパスに存在しない場合 | エラーメッセージ表示、再試行ボタン提供 |
| `ValueError: Not a CSV file` | 指定されたファイルが CSV 形式でない場合 | エラーメッセージ表示、ファイル選択画面へ遷移 |
| `ValueError: Too many columns` | 選択可能なカラムが 2 つ未満の場合 | エラーメッセージ表示、再試行ボタン提供 |
| `ValueError: Non-numeric data` | 選択されたカラムが数値型でない場合 | エラーメッセージ表示、再試行ボタン提供 |
| `ValueError: Empty data` | 選択されたカラムが空の場合 | エラーメッセージ表示、再試行ボタン提供 |
| `ValueError: Data length mismatch` | 2 カラムのデータ長が異なる場合 | エラーメッセージ表示、再試行ボタン提供 |
| `ValueError: Too many rows` | データ行数が 10,000 行を超える場合 | エラーメッセージ表示、警告 |

## テスト実行

### ユニットテスト

```bash
pytest tests/ -v
```

### E2E テスト

```bash
docker compose --profile test up test_playwright
```

## 制限事項

- ファイルサイズ：10MB 以内
- データ行数：10,000 行まで
- ファイル形式：CSV のみ

## ライセンス

MIT License

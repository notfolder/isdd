# Backend Dockerfile
# 要件ID: RQ-NF-FRAMEWORK-BASIC
# 設計ID: DS-MD-BACKEND-API-FT-LOGIN
# 要件概要: FastAPIを使用してバックエンドAPIを構築する
# 設計概要: Python 3.11を使用し、FastAPIアプリケーションを実行する

FROM python:3.11-slim

WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ポート8000を公開
EXPOSE 8000

# デフォルトコマンド（docker-compose.ymlでオーバーライドされる）
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

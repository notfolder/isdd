# Dockerfile for Streamlit Application
FROM python:3.10-slim

# 環境変数の設定（Pythonの出力バッファリングを無効化）
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# 依存ライブラリのインストール
# requirements.txt が存在しないため、明示的に必要なものを追加する (例: pandas, streamlit)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコンテナにコピー
COPY src/ /app/src
COPY utils/ /app/utils
COPY README.md .
# 他の必要なファイルを全てここに追記する必要がありますが、今回は主要なディレクトリのみコピーします。

# 実行コマンド (docker-compose.ymlで上書きされるため、ここではデフォルトを残す)
CMD ["streamlit", "run", "src/streamlit_app.py"]
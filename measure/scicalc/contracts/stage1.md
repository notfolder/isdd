# 採点の契約（sci-calc）

- 作業ディレクトリの直下に `pyproject.toml` と `src/sci_calc/` を置く（下位のフォルダに入れない）。
- 採点は `uv venv` と `uv pip install -e ".[dev]"` で環境を作り、`python -m uvicorn sci_calc.app:app` で起動して、HTTP の要求と応答を確かめる。
- URL、要求と応答の形、エラーコードは REQUEST.md の「API Specification」のとおりにする。
- Python は 3.13。パッケージの管理は uv。

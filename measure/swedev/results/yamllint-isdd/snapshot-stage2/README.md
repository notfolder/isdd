# yamllint（isdd の README）

YAML ファイルの書式を規則ごとに検査する Python パッケージと、コマンド `yamllint`。
利用の詳細（規則の一覧、設定の書き方、ライブラリの API）は英語の `README.rst` と `docs/` を参照。

## 起動方法

1. Python 3.8 以上の環境で、リポジトリのルートから `pip install .` を実行する（開発中は `pip install -e .`）。
2. 動作を確かめる: `yamllint --version` を実行し、版の番号が表示されれば成功。
3. 検査する: `yamllint <ファイルまたはディレクトリ>` を実行する。違反があれば終了コードは 1 になる。設定は、カレントディレクトリから親へ `.yamllint` を探し、無ければ既定の設定を使う。`-c <設定ファイル>` または `-d '<設定の文字列>'` で指定もできる。
4. 単体テスト: `python3 -m pytest tests`。E2E テスト: `python3 -m pytest e2e --junitxml=e2e/results/e2e.xml`。

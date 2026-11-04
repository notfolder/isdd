# num2words

数値を各言語の読み上げ文字列に変換する Python ライブラリです。詳しい説明は `README.rst` を参照してください。

## 起動方法

ライブラリのため、サーバーは起動しません。利用するプロジェクトに組み込んで import します。
このディレクトリの直下で次を実行すると、動作を確かめられます。

```bash
python3 -c "from num2words import num2words; print(num2words(21))"
```

認証（初期ユーザー）は無い。

## テスト

```bash
python3 -m pytest tests                              # 単体テスト・結合テスト
python3 -m pytest e2e --junitxml=e2e/results/e2e.xml  # E2E テスト（結果は e2e/results/）
```

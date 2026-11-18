# 題材 sci-calc（AI-DLC の評価器の題材で 3 群を比べる）

AI-DLC（awslabs/aidlc-workflows）の v1 系にある評価器 `scripts/aidlc-evaluator` の題材 `sci-calc` を、isdd の計測の実行器で回すためのフォルダ。

- 出どころ: https://github.com/awslabs/aidlc-workflows の `v1` ブランチ（コミット 188482a173a1a40c21cbd0837fe60326440d79eb、MIT-0）。
  - `stages/stage1.md` は `test_cases/sci-calc/vision.md` と `tech-env.md` をつないだもの（エージェントに渡す）。
  - `hidden/openapi.yaml` は `test_cases/sci-calc/openapi.yaml`（エージェントには見せない。`x-test-cases` の 88 件が採点）。
  - `vendor/contracttest/` は `packages/contracttest/src/contracttest/` の複製、`vendor/shared/` は `packages/shared/src/shared/` のうち契約テストが読む 3 ファイルの複製（どちらも手で編集しない）。
- 使わないもの: 評価器の「正解の AI-DLC 文書との意味的な類似度」（AI-DLC の文書の形が前提で、ほかの手法に当てられない）と、Bedrock での実行。
- 実行: `python3 measure/run.py --task scicalc --arm isdd|control|aidlc --run 1 --stages 1 --work <作業の親> ...`
- 採点だけ: `python3 measure/scicalc/score.py --app <アプリ> --out <JSON>`（uv が Python 3.13 を用意する）。
- 参考値（AI-DLC の公開している基準の実行、v1 の規則、Opus 4.6）: 契約テスト 88/88、約 24 分、980 万〜1,840 万トークン。

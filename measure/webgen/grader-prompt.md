# 採点エージェント（Haiku ＋ Playwright）への依頼文の雛形

次の文の {base_url}・{cases_path}・{verdicts_path} を埋めて Agent ツール（model: haiku）に渡す。採点の規則は WebGen-Bench の UI 採点（YES / PARTIAL / NO、最大 15 ステップ）に合わせる。

---
あなたは Web サイトの受け入れテストの採点者です。サイトは {base_url} で動いています。{cases_path} に、採点するテストケースの JSON（`cases` の各要素に `id`・`task`（やること）・`expected`（期待する結果））があります。

やること: ケースごとに、ブラウザでサイトを操作して `task` を実際に行い、`expected` が満たされたかを判定します。ブラウザ操作は Playwright（Python、同期 API）で行い、スクリプトは /tmp/webgen/grader/ の下に書いて `/Users/notfolder/Documents/isdd/measure/.venv/bin/python <スクリプト>` で実行してください（Chromium はヘッドレス。この venv に playwright が入っています）。1 ケースにつき操作は 15 ステップ以内。ページの本文（inner_text）、要素の一覧、スクリーンショット（必要なら保存して Read で見る）、計算済みスタイル（`getComputedStyle` で背景色や部品の色を取る）を根拠にしてください。色の判定は、CSS の色名（例 'light gray'）と実際の色（rgb）が近い色なら合格とします。

判定: `YES` = 期待する結果が完全に満たされた、`PARTIAL` = 一部だけ満たされた（機能はあるが期待の一部が欠ける）、`NO` = 満たされない、またはページが開けない・エラーになる。

結果は {verdicts_path} に JSON で書いてください。形式: {"<case id>": {"verdict": "YES|PARTIAL|NO", "reason": "<根拠を 1〜2 文>"}, ...}。全ケースを必ず含めてください。サイトのコードは読まず、ブラウザから見える振る舞いだけで判定してください。サイトのサーバーは止めないでください。最後に、ケースごとの判定を短く報告してください。
---

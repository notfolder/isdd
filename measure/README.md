# isdd の効果の計測（計測 1: 備品管理アプリの試運転）

`.history/BACKLOG.md` の「isdd の効果の計測」の計測 1。公開ベンチマークには「変更を重ねて文脈を切り替える」題材が無いので、自作の題材で仕組みを通す。

## 設計（ユーザー決定 2026-11-04）

- 題材: 備品管理・貸出管理アプリ（ブランチ `feature-equipment-lending-management` の要件と E2E から）。3 段に分ける（`stages/`）。段 1 は新規の要件、段 2・3 は変更要求。
- 群: isdd 群（v2.2.0 のスキルを `.claude/skills/` に入れ、isdd-spec → isdd-build を通す）と対照群（スキル無し）。どちらも各段の依頼の文章（`stages/stageN.md`）と採点の契約（`contract.md`）だけを受け取る。isdd 群のヒアリングは `answers.md` の固定回答で通す。
- セッション: 段ごとに新しい `claude -p`（会話は引き継がない。前の段の成果物だけが残る）。
- モデル: 両群 Haiku（`claude-haiku-5-5`）。0 点に近ければ Sonnet でも回す。課金はサブスクリプション。
- 回数: 各群 2 回。
- 隠しテスト: ブランチの E2E 18 本を契約に合わせて書き直したもの（`hidden/`）。各段の後に、その段までのテストを全部回す。
- 測るもの: 段ごとの通過率、最終の通過率、退行数（前の段で通ったテストが後で落ちた数）、作りすぎ（契約に無い URL、公開関数の数）、トークンと往復数、所要時間。

## 使い方

```bash
# 隠しテストの採点環境（Playwright）
python3 -m venv .venv && .venv/bin/pip install -r hidden/requirements.txt && .venv/bin/playwright install chromium
# 1 群 1 回を 3 段通す（作業ディレクトリは WORK の下）
python3 measure/run.py --arm isdd --run 1 --model claude-haiku-5-5 --work /path/to/work
# 採点だけ
python3 measure/score.py --app /path/to/work/isdd-r1 --stage 2 --out measure/results/isdd-r1-stage2.json
```

結果は `results/` に JSON で残す（作業ディレクトリとコードは残さない）。

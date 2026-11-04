# isdd の効果の計測（計測 1: 備品管理アプリ、計測 2: SWE-Dev、計測 4: WebGen-Bench）

`.history/BACKLOG.md` の「isdd の効果の計測」の計測 1。公開ベンチマークには「変更を重ねて文脈を切り替える」題材が無いので、自作の題材で仕組みを通す。

## 設計（ユーザー決定 2026-11-04）

- 題材: 備品管理・貸出管理アプリ（ブランチ `feature-equipment-lending-management` の要件と E2E から）。3 段に分ける（`stages/`）。段 1 は新規の要件、段 2・3 は変更要求。
- 群: isdd 群（v2.2.0 のスキルを `.claude/skills/` に入れ、isdd-spec → isdd-build を通す）と対照群（スキル無し）。どちらも各段の依頼の文章（`stages/stageN.md`）と採点の契約（`contract.md`）だけを受け取る。isdd 群のヒアリングは `answers.md` の固定回答で通す。
- セッション: 段ごとに新しい `claude -p`（会話は引き継がない。前の段の成果物だけが残る）。
- モデル: 両群 Haiku（`claude-haiku-5-5`）。0 点に近ければ Sonnet でも回す。課金はサブスクリプション。
- 回数: 各群 2 回。
- 隠しテスト: ブランチの E2E 18 本を契約に合わせて書き直したもの（`hidden/`）。各段の後に、その段までのテストを全部回す。
- 測るもの: 段ごとの通過率、最終の通過率、退行数（前の段で通ったテストが後で落ちた数）、作りすぎ（契約に無い URL、公開関数の数）、トークンと往復数、所要時間。

## 実行のしかた（2 通り）

- `run.py`: 段ごとに `claude -p` を起こして無人で回す（`--permission-mode acceptEdits --allowedTools ...`）。この方式は Claude Code の自動モードの分類器に「無人のエージェントの作成」として止められることがある。止められたら、ユーザーが権限の規則を足すか、下の方式を使う。
- `stage.py` ＋ Agent ツール: `stage.py prepare` で段の作業ディレクトリを用意し、Claude Code のセッションから Agent ツール（モデル haiku、新しいエージェント＝新しい文脈）で段の依頼を実行し、`stage.py finish` で採点して記録する。2026-11-04 の試運転はこの方式（`run.py` が止められたため）。トークン数と往復数は取れないので、所要時間と通過率・退行・作りすぎだけを記録する。

## 使い方

```bash
# 隠しテストの採点環境（Playwright）
python3 -m venv .venv && .venv/bin/pip install -r hidden/requirements.txt && .venv/bin/playwright install chromium
# 1 群 1 回を 3 段通す（作業ディレクトリは WORK の下。python3 を 3.12 にする bin を PATH の先頭に足す）
python3 measure/run.py --arm isdd --run 1 --model claude-haiku-5-5 --work /path/to/work --path-prefix /path/to/bin
# Agent ツールで回すとき
python3 measure/stage.py prepare --arm control --run 1 --stage 1 --work /path/to/work
#   → Agent ツールで依頼を実行（作業ディレクトリ、REQUEST.md、contract.md、STAGE_DONE の約束を伝える）
PATH=/path/to/bin:$PATH python3 measure/stage.py finish --arm control --run 1 --stage 1 --work /path/to/work --wall-sec 600
# 採点だけ
python3 measure/score.py --app /path/to/work/isdd-r1 --stage 2 --out measure/results/isdd-r1-stage2.json
```

結果は `results/` に JSON で残す（作業ディレクトリとコードは残さない）。

## 2026-11-04 の本計測での変更

- 契約と固定回答を段ごとに分けた（`contracts/stageN.md` は累積で `contract.md` にまとめて渡す。`answers/stageN.md`）。試運転の結果は `results/trial-2026-11-04/`。
- `run.py` は `claude -p` の権限指定を `evals/run-claude-code.py` と同じ形（標準入力で依頼、`--permission-mode acceptEdits`、`--allowedTools` の列挙、`--setting-sources project`）に直したが、Claude Code の自動モードの分類器が「無人のエージェントの作成」として止めるため、本計測は `stage.py`（prepare → Agent ツール（haiku）→ finish → score）で回した。
- `stage.py finish` は snapshot と記録だけ、`stage.py score` が snapshot を採点する（`results/.score.lock` で直列）。採点は `PATH=/tmp/isdd-measure/bin:$PATH`（python3 を 3.12 にする）で回す。
- 計測 2（SWE-Dev easy、`swedev/`）: 1 パッケージを 1 作業ディレクトリにし、課題を段として積む。`swedev.py prepare` が Docker イメージから `/app/<pkg>` を取り出し、**正解の複製（build/lib、egg-info、modified_testcases、バイトコード）を消し**、課題で削られた関数を AST で消す。`evaluate` は作業ディレクトリの src をコンテナにマウントして隠しテスト（課題の test_code をコンテナに書く）を回す。
- 計測 4（WebGen-Bench、`webgen/`）: 3 課題（000010、000026、000088）を新規 → 変更 × 2 の 3 段にした（変更の依頼とケースは `plan.json`）。採点は Haiku ＋ Playwright の採点エージェント（`grader-prompt.md`）で YES / PARTIAL / NO。
- 計測 3（FeatureBench fast、`featurebench/`）: mlflow の課題 4 件（同じ base commit）を段として積む。`fb.py prepare` がイメージの /testbed を SSD に取り出し（.git と build/ は消す）、マスク patch と F2P テストの削除を当て、コンテナ `fb-<arm>` に /testbed としてマウントする。エージェントは `docker exec` でテストを回す。`evaluate` は test_patch を逆適用して F2P を戻し、最終段だけ P2P（全課題分）も回す（1 ファイル 15 分かかるものがある）。Docker は OrbStack でデータは /Volumes/SSD。

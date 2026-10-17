# スキル全体のレビューと重大 4 件＋残り 15 件の修正、Haiku のみの eval 運用へ

更新: 2026-10-18 03:12 JST
セッション: 10c5fdca-0022-47b4-9540-73bedfe90ca4
ログ: ./session.md

## 概要

全 11 スキルと共通リファレンス・チェッカーをレビューして 19 件を挙げ、全件修正して Haiku のみの eval（昇格なし）で 8 スキル合格を確認し、Sonnet 昇格の仕組みを削除した。

## やったこと

- **レビュー**（読み取りとスクラッチ領域での実測のみ）。重大 4 件: 変更フローで `check.sh` が `docs/detail_design.md` しか読まず変更設計の DS-ID が実装中ずっとエラーになる、逆引きスキルと PIR の責務が循環する、`trace_map_checker.py` が 5 言語以外を全行エラーにする（C# と TS アロー関数で実測）、docker compose・Playwright・初期ユーザーを無条件に要求する。中程度 11 件（`rq_ds_link_checker.py` が問題検出でも終了コード 0、変更要件書で RQ-BZ 必須の誤検知、`.agents/skills/...` 固定パス、未定義サブエージェントの起動指示、外部調査スキルの ID コメント残骸、MVP 適合性の自己矛盾など）、軽微 4 件（誤字、重複行、見出しレベルなど）。
- **phase 1（重大 4 件）**: `isdd-change-design` が確定時に正本へ反映する方式へ（PIR は安全網）。`isdd-reverse-engineering` が自分で正本を確定し、次のステップを `isdd-change-req` に。`trace_map_checker.py` を記号確認 5 言語＋ファイル存在確認の多言語に拡張。`isdd-setup` が `scripts/isdd/completeness.json`（実行形態・認証・外部連携）を生成し、`implementation_completeness_checker.py` がそれに従う。設計章立て第 9・11 章、tasks.md 固定タスク、実装スキル完了判定を条件付きに。eval 全 8 スキル Haiku 1 回目 PASS（22:24〜23:00）。
- **phase 2（残り 15 件）**: 上記の中程度・軽微を全件修正。eval は 6 スキル 1 回目 PASS、`isdd-design`（RQ-DS 対応表の章を作らなかった）と PIR 未マッピング検出（一覧を文章で済ませた）が 1 回目 FAIL。設計章立てに「12. 要件と設計の対応表」を必須章として追加、PIR 手順 5 に一覧の表形式を固定して再テストし、両方 1 回目 PASS（3:01〜3:07）。
- **eval 実行の見直し**: `run-all.sh` から Sonnet 昇格を削除（`WAZA_CLAUDE_MODEL` に統一、旧名互換）。`.env` の読み込みが環境変数を上書きしていた不具合を修正。`timeout_seconds` を実測の約 3 倍（600〜900 秒）に短縮し、`local` モードは `WAZA_LOCAL_TIMEOUT_SCALE`（既定 10）倍の一時ファイルで実行。
- **実行基盤の固まり**: phase 2 の実行で PIR の再試行（4 ケース目）と isdd-setup の 1 回目が、モデル応答待ちのまま 22〜40 分停止。転記ファイル未作成・Copilot プロセス生存で、スキルではなく Copilot CLI と API 間の問題と判断してプロセスを終了。eval の結果表で isdd-setup の 1 回目 FAIL はこの固まり。
- **コミット**: 3 コミット（重大 4 件 / 残り 15 件 / eval 実行の見直し）。複数 phase にまたがるファイルは主な phase のコミットに入れた。
- **意図的に残したもの**: `.env` の旧変数 3 行（`WAZA_CLAUDE_MODEL_PRIMARY` は互換で読まれ、他 2 行は無視される。git 管理外なのでユーザーが消す）。`gen_eval_metadata.py` は skill-creator 用として注記のみ。
- **環境メモ**: `gh skill install` はエージェントごとのディレクトリに置く（Claude Code は `.claude/skills/`、ユーザースコープはホーム配下。`gh skill install --help` で確認、gh 2.97.0）。Python 3.9.6 のため `str | None` は使わず `Optional`。bash は `set -u` 下で `$var（` のように全角括弧が続くと変数名の解釈が壊れるので `${var}` にする。

## 決定事項

- **eval は Haiku のみで回し、1 回目で落ちたらスキルの質の問題として SKILL.md を直す。Sonnet への昇格は使わない**（ユーザー指示 2026-10-17）。同じモデルでの 1 回だけの再試行は残す。
- **変更設計の正本反映は `isdd-change-design` の完了時に行う**（私の判断。`check.sh` が正本の設計書だけを読む構造上、実装前に正本が最新である必要があるため。`.history` 配下は変更の記録として残す）。
- **逆引きスキルは PIR を呼ばず自分で正本を確定し、完了後の新要求は変更フローへ**（私の判断。PIR の適用範囲宣言との矛盾と、`isdd-requirements` との循環を解消するため）。
- **eval のタイムアウトは実測の約 3 倍に短縮**（ユーザー選択 2026-10-18、案 A）。
- **コミットは 3 分割**（ユーザー選択 2026-10-18、案 B）。
- **10 分以上かかる作業は終了時刻を時計で報告し、同時に背景の待機コマンドで自分を起こす。見込みを超えたら進捗を確認して報告する**（ユーザー指示 2026-10-17。`~/.claude/CLAUDE.md` に強い指示として追記済み、未コミット）。

## 次にやること

- `.env` の旧変数 3 行を削除する（ユーザー作業）。
- `~/.claude/CLAUDE.md` の追記をホーム直下のセッションでコミット・push する。
- 実行基盤の固まり（Copilot CLI と Anthropic API 間でモデル応答待ちのまま停止）が再発するか観察する。再発するなら Copilot CLI の版を上げるか、検証 D（Claude Code 実行器）を優先する。
- v1.0.15 として `gh skill publish ./skills --tag v1.0.15` する前に、README の変更履歴を読み直す。

## バックログ

- [x] (2026-10-18) スキル全体のレビューと 19 件の修正（重大 4 件・中程度 11 件・軽微 4 件）。Haiku のみの eval で 8 スキル合格
- [x] (2026-10-18) `run-all.sh` から Sonnet 昇格を削除し、`.env` の優先順位とタイムアウト（実測の約 3 倍）を見直し
- [-] (2026-10-18) 検証のモデルを Haiku 既定・Sonnet 自動昇格にする運用 — ユーザー指示で昇格を廃止。Haiku で落ちたらスキルの質の問題として直す
- [ ] `.env` の旧変数 3 行（`WAZA_CLAUDE_MODEL_PRIMARY`・`WAZA_CLAUDE_MODEL_SECONDARY`・`WAZA_CLAUDE_ESCALATE`）を削除する（ユーザー作業）
- [ ] 実行基盤の固まり（phase 2 で 2 回。モデル応答待ちで 22〜40 分停止）の再発を観察し、再発するなら Copilot CLI の更新か検証 D を優先する
- [ ] v1.0.15 を `gh skill publish ./skills --tag v1.0.15` で公開する（README の変更履歴を読み直してから）

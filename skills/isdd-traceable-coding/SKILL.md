---
name: isdd-traceable-coding
description: >
  要件定義書と詳細設計書（docs/requirements.md・docs/detail_design.md）にもとづいて実装し、
  設計 ID とコードの対応を対応表（docs/trace_map.md）に記録して、チェッカーで整合を確かめる。コードには ID を書かない。
  「実装して」「設計書どおりに実装して」「tasks.md を進めて」「対応表を更新して」「isdd の実装ルールを適用して」といった依頼で使う。
  設計書に無い設計要素が必要になったときは実装を止め、設計スキル（isdd-design / isdd-change-design）に戻す。
license: CC-BY-4.0
metadata:
  version: "v2.0.0"
---

# isdd-traceable-coding — トレーサブル実装スキル

詳細設計書の設計要素を 1 対 1 でコードに落とし、設計 ID とコードの対応を対応表 `docs/trace_map.md` に記録する。

## このスキルのファイル

参照ファイルはこのスキルの `references/`、チェッカーは `scripts/` にある。下のコマンドは `.agents/skills/` に入れた場合のパスで書いている。別の場所（`.claude/skills/`、`.github/skills/`、ホーム配下など）に入れた場合は、この SKILL.md があるディレクトリに読み替える。

| ファイル | 使う場面 |
|---|---|
| `references/trace-map-rules.md` | 対応表の書式・粒度・チェックの意味 |
| `scripts/rq_ds_link_checker.py` | 要件 ID と設計 ID の対応チェック |

対応表チェックと実装完了チェックは、`isdd-setup` がプロジェクトに入れた `scripts/isdd/` のものを使う（pre-commit と同じものを動かすため）。

## 始める前に確かめること

次を bash で確かめる。

```bash
ls scripts/isdd/check.sh scripts/isdd/trace_map_checker.py scripts/isdd/implementation_completeness_checker.py
cat scripts/isdd/VERSION
```

- ファイルが無い場合は、作業を止めて `isdd-setup` を先に実行するよう案内する。チェッカーが無いと完了条件を確かめられないため。
- 版を比べる。`cat scripts/isdd/VERSION` の出力と、この SKILL.md の先頭（frontmatter）にある `metadata.version` の値（`v` で始まる版番号）を、1 文字ずつ同じか比べる。
  - 同じなら次へ進む。
  - VERSION が無いか、違う場合は、作業を始める前に「scripts/isdd/VERSION（読んだ値）とスキルの版（metadata.version の値）が違うため、isdd-setup を再実行します」と報告し、`isdd-setup` を再実行してから進める。古いチェッカーで判定すると、規則の変更を見落とすため。`isdd-setup` は何度実行しても同じ状態になる。
  - 比べた結果（両方の値と、再実行したか）を最終報告に書く。
- `docs/requirements.md` と `docs/detail_design.md` があり、`rq_ds_link_checker.py` が問題 0 件であること。

## 守ること

- 要件 ID と設計 ID の正本は `docs/requirements.md` と `docs/detail_design.md` だけ。
- コードに要件 ID・設計 ID を書かない。コメントは言語の流儀に従った通常のドキュメントコメント（処理の説明、引数、戻り値）だけにする。対応は対応表で持つので、コードに書くと二重管理になり、ずれるため。
- ID を採番しない。設計書に無い設計要素が要るとわかったら、コーディングを止めて `docs/proposals.md` に提案を書き、`isdd-design` か `isdd-change-design` で設計を直してから再開する。採番を設計スキルに限ると、設計書と対応表の ID が常に一致するため。
- 正本（`docs/requirements.md`・`docs/detail_design.md`）は書き換えない。実装中に見つけた要件・設計の不足や矛盾は `docs/proposals.md` に書く。正本への反映は `isdd-post-implementation-review` が行い、完了時に `docs/proposals.md` を削除する。
- 削除された要件・設計に対応するコードは削除し、対応表の行も削除する。
- 既存コードがある場合、設計の範囲外のロジックは変えない。

## 対応表

書式と粒度は `references/trace-map-rules.md` に従う。要点:

- 列は「DS-ID」「修飾名」「備考」の 3 列。
- 修飾名は `ファイルパス`（DS-MD）、`ファイルパス::名前`（クラス・関数）、`ファイルパス::クラス名.名前`（メソッド）。
- 載せるのはファイル、クラス、公開関数・メソッド。アンダースコア始まりの内部関数、ダンダーメソッド、テストファイルは載せない。
- クラス・公開関数・ファイルを追加、改名、削除したら、同じ作業の中で対応表を更新する。

## 手順

tasks.md がある場合は、そのタスクを上から順に進める。無い場合は次の順に進める。

1. `docs/requirements.md` と `docs/detail_design.md` を読み、要件 ID と設計 ID をすべて把握する。
2. 設計要素（DS-MD、DS-CL、DS-FN、DS-IF、DS-BT、DS-EV）ごとに実装する。
3. 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する。対応がわからない要素はユーザーに確認する。
4. 対応表の整合を確かめる。エラーも警告も 0 件になるまで、コードか対応表を直す。

   ```bash
   bash scripts/isdd/check.sh --strict
   ```

5. 要件 ID と設計 ID の対応を確かめる。問題があれば終了コード 1 になる。

   ```bash
   python3 .agents/skills/isdd-traceable-coding/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md
   ```

6. 実装完了の条件を確かめる。要求される項目は `scripts/isdd/completeness.json`（詳細設計書の実行形態・認証・外部連携から生成）で決まる。

   ```bash
   python3 scripts/isdd/implementation_completeness_checker.py .
   ```

   - 出力の冒頭の「実行形態 / 認証 / 外部連携」が詳細設計書と合っているか確かめる。違えば `isdd-setup` を正しい値で再実行する。
   - FAIL があれば直して再実行する。よくある FAIL と直し方:
     - `docker-compose.yml が見つかりません`（実行形態がコンテナの場合だけ出る）→ docker-compose.yml を作る
     - `e2e/ ディレクトリが存在しません` → 詳細設計書 第 8 章のとおり E2E テストを `e2e/` に作る
     - `README.md に不足があります` → 起動方法（認証がある場合は初期ユーザー情報も）を README.md に書く
     - `docs/trace_map.md が見つかりません` → 対応表を作る
7. 詳細設計書 8-1 の実行コマンドで単体テストと結合テストが全件通ること、第 9 章の起動方法で起動または実行できること、8-4 の実行コマンドで E2E テストが全件通ること（外部連携がある場合は mock モード）を確かめる。
8. 要件・設計との対応漏れが無いかを見直し、ユーザーに報告する。

## 完了条件

次をすべて満たしてから完了を報告する。満たしていない項目があれば、完了ではなく残っている項目として報告する。

- `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で、実行ログを応答に載せた
- `rq_ds_link_checker.py` が問題 0 件で、実行ログを応答に載せた
- `implementation_completeness_checker.py` が全項目 OK で、実行ログを応答に載せた
- 詳細設計書 8-1 の実行コマンドで単体テストと結合テストが全件通った
- 第 9 章の起動方法で起動または実行できた（実行形態がコンテナなら `docker compose up`）
- E2E テストが `e2e/` にあり、詳細設計書 8-4 の実行コマンドで全件通った（外部連携がある場合は mock モード）
- `README.md` に「起動方法」がある（認証がある場合は「初期ユーザー」も）
- コードに `要件ID:` `設計ID:` `RQ-` `DS-` を含むコメントが無い
- `scripts/isdd/VERSION` とこの SKILL.md の `metadata.version` を比べた結果を報告に書いた

## 次のステップ

完了を報告するときに、`isdd-post-implementation-review` で実装後の逆引き整合チェックを行い、要件・設計・対応表の正本を確定するよう提案する。

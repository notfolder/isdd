---
name: isdd-change-design
description: >
  変更要件定義書（.history/[YYYYMMDD]-[タスク名]/change_requirements.md）から、既存設計との整合を保った
  変更詳細設計書（change_detail_design.md）を作り、確定後に正本（docs/requirements.md・docs/detail_design.md）へ反映して、
  実装タスクの一覧（tasks.md）を作る。「変更設計書を作って」「既存設計への差分設計をまとめて」
  「change_requirements から詳細設計を作成して」といった依頼で使う。要件定義書からの新規設計は isdd-design が扱う。
license: CC-BY-4.0
metadata:
  version: "v1.0.15"
---

# isdd-change-design — 変更詳細設計スキル

既存の要件定義書と設計書を理解したうえで、変更要件定義書の [追加] [削除] を設計の差分に落とし、確定したら正本へ反映する。

## このスキルのファイル

参照ファイルはこのスキルの `references/`、チェッカーは `scripts/` にある。下のコマンドは `.agents/skills/` に入れた場合のパスで書いている。別の場所（`.claude/skills/`、`.github/skills/`、ホーム配下など）に入れた場合は、この SKILL.md があるディレクトリに読み替える。

| ファイル | 使う場面 |
|---|---|
| `references/design-chapters.md` | 設計書の章立てと技術選定の手順 |
| `references/requirement-exclusion.md` | 最小設計の意味、[追加] 要件を外すときの手順、設計中に見つけた要件の不足の扱い |
| `references/design-completeness.md` | 設計書の網羅性チェック |
| `references/design-tasks-rules.md` | tasks.md の書き方 |
| `references/id-definitions.md` | 設計 ID の採番と変更管理 |
| `references/trace-map-rules.md` | 対応表（コード設計章で触れる） |
| `references/document-rules.md` | 文書の書き方と、作成後のレビュー |
| `scripts/rq_integrity_checker.py` | 要件 ID の整合チェック（正本への反映後） |
| `scripts/rq_ds_link_checker.py` | 要件 ID と設計 ID の対応チェック（正本への反映後） |

## 入力と出力

- 入力: `.history/[YYYYMMDD]-[タスク名]/change_requirements.md`。ユーザーの指定が無ければ、`.history/` 配下から対象を確かめる。
- 出力: 同じディレクトリの `change_detail_design.md` と `tasks.md`、および反映後の `docs/requirements.md` と `docs/detail_design.md`。
- `.history/` 配下の変更要件定義書と変更設計書は変更の記録として残し、反映後も書き換えない。

## 始める前に確かめること

- 外部連携がある場合: `isdd-external-research` の整合確認が終わり、未解消の不整合が無いこと。
- `docs/requirements.md` と `docs/detail_design.md` を読み、既存の仕様を理解する。

## 正本を書き換える時期

変更設計書のレビューに合格するまでは、`docs/requirements.md` と `docs/detail_design.md` を書き換えない。合格したら「正本への反映」で両方を更新する。
実装スキルと対応表チェック（`scripts/isdd/check.sh`）は正本の `docs/detail_design.md` だけを読むので、ここで反映しないと、変更設計の設計 ID が実装中ずっと「設計書に無い」エラーになるため。

## 最小設計と要件の除外

`references/requirement-exclusion.md` に従う。このスキルの「入力要件書」は `change_requirements.md` の [追加] 要件を指す。

- [追加] 要件（`RQ-BK`・`RQ-BZ`・`RQ-EF` を除く）はすべて変更設計に反映する。外せるのは既存設計か他の要件の設計で実現済みの要件だけで、ユーザーの承認を得て「11-1. 除外要件」に吸収先の設計 ID を記録する。実装できない・矛盾する要件は、除外せずに `change_requirements.md` を直す。
- 変更要件定義書に無い設計要素は足さない。
- 設計中に未マッピングが出たら、1 件ずつユーザーに聞き直して `change_requirements.md` を直し、変更設計書に伝える。直した要件 ID と理由は tasks.md の末尾にも書く。

## 技術選定

既存設計 `docs/detail_design.md` の言語・フレームワーク・DB を引き継ぐ。変更要件の技術制約がそれと矛盾する場合だけ、`references/design-chapters.md` 第 1 章の手順（インターネット調査、比較表、ユーザー承認）で選び直す。
選び直しが必要なのに検索・取得ツールが使えない場合は、推測で選ばず「インターネット調査ができないため技術選定を確定できない」と報告して止まる。

## 変更設計書の書き方

- 章立ては `references/design-chapters.md` に従う。第 11 章「要件と設計の対応表」には、[追加] と [削除] の設計 ID を 1 行ずつ並べる。
- すべての設計要素に [追加] か [削除] を書く。「変更」という区分は使わず、変える要素は旧要素を [削除]、新要素を [追加] に分けて書く。
- 削除する要素には削除理由を書く。
- CRUD テーブルは、変更の有無にかかわらず全エンティティ分を書く。
- 変更が無い章は「変更なし。既存設計 `docs/detail_design.md` セクション[N] を参照」とだけ書く。
- すべての設計要素に `references/id-definitions.md` に従って `DS-*` を付け、対応する `RQ-*` と結びつける。どの種類の設計 ID で受けるかは、同ファイルの「要件カテゴリと設計 ID の対応先」に従う。ソースファイルを追加する場合は、第 7 章のファイル一覧で `DS-MD-*` を付ける。ID は表の専用列に書き、本文や図には書かない。
- 同じ意味の処理を 2 回作らず、共通化の方針を書く。
- 確認が要るのは、要件レベルの不足（外部連携の API 仕様、外部スキーマなど）だけにする。それ以外はユーザーに確認せず進める。
- 文書の書き方は `references/document-rules.md` に従う。

設計・検証・修正を繰り返し、網羅性チェックとレビューが終わるまで続ける。

## 網羅性チェック

`references/design-completeness.md` の項目をすべて確認し、既存設計書との整合も確かめる。不足があれば直す。

## レビュー

`references/document-rules.md` のレビュー項目に加えて、次を確認する。問題があれば直してから報告する。

1. 冗長な設計が無いか
2. 網羅性チェックをすべて満たしているか
3. 未マッピングが出た場合、変更要件への反映と設計 ID への伝播が終わっているか

合格したら `.history/[YYYYMMDD]-[タスク名]/change_detail_design.md` を保存し、正本への反映に進む。

## 正本への反映

反映する前に、反映する要件 ID と設計 ID の一覧（追加・削除）をユーザーに示す。

1. `docs/requirements.md` を更新する。
   - [追加] 要件を該当章へ足し、[削除]（`deprecated`）要件とその ID を消す。
   - 業務課題一覧と、業務課題と要件の対応表を変更後の状態にする。技術制約（1-1）に変更があれば書き換える。
   - 全章を通読し、変更前の挙動を前提にした本文（概要、データ章、用語定義、旧機能名・旧画面名への言及）を変更後の内容に書き換える。ID の表だけを差し替えると、本文が旧仕様のまま残るため。
2. `docs/detail_design.md` を更新する。
   - [追加] 設計要素を該当章へ足し、[削除] 設計要素とその ID を消す。
   - 1 と同じく全章を通読し、旧設計を前提にした本文（構成図、処理フロー、クラス図、ファイル一覧、要件と設計の対応表）を書き換える。
   - 変更設計書の「11-1. 除外要件」の行を、`docs/detail_design.md` の 11-1 に書き写す（書き写さないと、正本どうしのチェックで除外した要件が未マッピングになるため）。
   - 正本には [追加] [削除] の区分を書かない。正本は現在有効な内容だけを持つ。
3. 次を bash で実行し、両方が合格するまで正本を直す。

   ```bash
   python3 .agents/skills/isdd-change-design/scripts/rq_integrity_checker.py docs/requirements.md
   python3 .agents/skills/isdd-change-design/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md
   ```

4. 反映した要件 ID・設計 ID の一覧と、書き換えた本文の箇所をユーザーに報告する。

反映後に実装で見つかる差分と、ここでの反映漏れは、`isdd-post-implementation-review` が拾う。

## tasks.md

反映が終わったら、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を `references/design-tasks-rules.md` に従って作る。先頭の固定タスクには「正本反映の確認タスク」も入れる。
設計中に `change_requirements.md` を直した場合は、直した要件 ID と理由、`change_detail_design.md` への伝播を確認するタスクを末尾に書く。

## 完了条件

- `change_detail_design.md` と `tasks.md` を保存した
- `docs/requirements.md` と `docs/detail_design.md` に変更を反映した（[追加] [削除] の区分は正本に残さない）
- `rq_integrity_checker.py` と `rq_ds_link_checker.py` を正本に対して実行し、合格した実行ログを応答に載せた

## 次のステップ

完了を報告するときに、次のスキルを提案する。

- `scripts/isdd/check.sh` が無いプロジェクトでは、先に `isdd-setup` で対応表チェックを導入する
- `isdd-traceable-coding` で変更設計にもとづく実装と対応表の更新を行う

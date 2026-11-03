---
name: isdd-change-design
description: >
  変更要件定義書（.history/[YYYYMMDD]-[タスク名]/change_requirements.md）から、既存設計との整合を保った
  変更詳細設計書（change_detail_design.md）と実装タスクの一覧（tasks.md）を作り、進行中の変更として登録する。
  正本（docs/requirements.md・docs/detail_design.md）は書き換えない（反映は実装後に isdd-post-implementation-review が行う）。「変更設計書を作って」「既存設計への差分設計をまとめて」
  「change_requirements から詳細設計を作成して」といった依頼で使う。要件定義書からの新規設計は isdd-design が扱う。
license: CC-BY-4.0
metadata:
  version: "v2.0.1"
---

# isdd-change-design — 変更詳細設計スキル

既存の要件定義書と設計書を理解したうえで、変更要件定義書の [追加] [削除] を設計の差分に落とし、確定したら進行中の変更として登録する。

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
| `scripts/rq_integrity_checker.py` | 変更要件定義書の要件 ID の整合チェック |
| `scripts/rq_ds_link_checker.py` | 変更要件定義書と変更設計書の要件 ID・設計 ID の対応チェック |

## 入力と出力

- 入力: `.history/[YYYYMMDD]-[タスク名]/change_requirements.md`。ユーザーの指定が無ければ、`.history/` 配下から対象を確かめる。
- 出力: 同じディレクトリの `change_detail_design.md` と `tasks.md`、および進行中の変更を指す `docs/active_change`。
- `.history/` 配下の変更要件定義書と変更設計書は変更の記録として残し、正本への反映後も書き換えない。

## 始める前に確かめること

- 外部連携がある場合: `isdd-external-research` の整合確認が終わり、未解消の不整合が無いこと。
- `docs/requirements.md` と `docs/detail_design.md` を読み、既存の仕様を理解する。

## 正本を書き換えない

このスキルでは `docs/requirements.md` と `docs/detail_design.md` を書き換えない。正本は「実装済みの仕様」だけを持ち、変更は実装が終わってから `isdd-post-implementation-review` が反映する。実装の前に書き換えると、実装をやめたり途中で止まったりしたときに、作っていない仕様が正本に残るため。
実装中は、`docs/active_change` が指す変更設計書を対応表チェック（`scripts/isdd/check.sh`）と実装スキルが正本に重ねて読むので、変更設計の設計 ID はエラーにならない。

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

合格したら `.history/[YYYYMMDD]-[タスク名]/change_detail_design.md` を保存し、整合チェックに進む。

## 整合チェック

変更設計書を保存したら、次を bash で実行し、両方が合格するまで変更要件定義書と変更設計書を直す。`[YYYYMMDD]-[タスク名]` は実際のディレクトリ名に置き換える。実行ログは応答に載せる。

```bash
python3 .agents/skills/isdd-change-design/scripts/rq_integrity_checker.py .history/[YYYYMMDD]-[タスク名]/change_requirements.md
python3 .agents/skills/isdd-change-design/scripts/rq_ds_link_checker.py .history/[YYYYMMDD]-[タスク名]/change_requirements.md .history/[YYYYMMDD]-[タスク名]/change_detail_design.md --base docs/requirements.md
```

`--base` に正本の要件定義書を渡すと、変更設計書が既存の要件（変更要件定義書に無い `RQ-*`）を参照していても未定義参照にならない。

## 進行中の変更の登録

整合チェックに合格したら、`docs/active_change` に変更のディレクトリのパス（例: `.history/20250115-add-user-profile/`）を 1 行だけ書く。
`scripts/isdd/check.sh` はこのファイルがあれば変更設計書を正本に重ねて判定し、`isdd-post-implementation-review` は正本へ反映し終えたらこのファイルを消す。別の変更が登録済み（`docs/active_change` が別のディレクトリを指している）なら書き換えず、先にその変更を `isdd-post-implementation-review` で正本へ反映するようユーザーに伝えて止まる。変更を重ねると、どの差分がどの変更のものか分からなくなるため。

## tasks.md

登録が終わったら、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を `references/design-tasks-rules.md` に従って作る。先頭の固定タスクには「進行中の変更の登録確認タスク」も入れる。
設計中に `change_requirements.md` を直した場合は、直した要件 ID と理由、`change_detail_design.md` への伝播を確認するタスクを末尾に書く。

## 完了条件

- `change_detail_design.md` と `tasks.md` を保存した
- `rq_integrity_checker.py` と `rq_ds_link_checker.py` を変更要件定義書と変更設計書に対して実行し、合格した実行ログを応答に載せた
- `docs/active_change` に変更のディレクトリのパスを書いた
- `docs/requirements.md` と `docs/detail_design.md` を書き換えていない

## 次のステップ

完了を報告するときに、次のスキルを提案する。

- `scripts/isdd/check.sh` が無いプロジェクトでは、先に `isdd-setup` で対応表チェックを導入する
- `isdd-traceable-coding` で変更設計にもとづく実装と対応表の更新を行う
- 実装が終わったら `isdd-post-implementation-review` で変更を正本へ反映する

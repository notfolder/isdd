---
name: isdd-design
description: >
  要件定義書（docs/requirements.md）から、要件をすべて反映し要件に無いものを足さない詳細設計書（docs/detail_design.md）と、
  実装タスクの一覧（tasks.md）を作る。isdd の第 2 ステップ。技術選定、網羅性の確認、冗長な設計の削除、要件と設計の対応付けまで行う。
  「詳細設計して」「設計書を作りたい」「要件から設計に落として」「内部設計まで詰めたい」といった依頼で使う。
  変更要件定義書（change_requirements.md）からの差分設計は isdd-change-design が扱う。
license: CC-BY-4.0
metadata:
  version: "v1.0.15"
---

# isdd-design — インタビュー駆動 詳細設計スキル

要件定義書をもとに、矛盾が無く、要件をすべて満たす最小の詳細設計書を作る。
実装スキルは設計書の設計要素だけを実装するので、設計書に無いものは作られず、設計書にあるものはすべて作られる前提で書く。

## このスキルのファイル

参照ファイルはこのスキルの `references/`、チェッカーは `scripts/` にある。下のコマンドは `.agents/skills/` に入れた場合のパスで書いている。別の場所（`.claude/skills/`、`.github/skills/`、ホーム配下など）に入れた場合は、この SKILL.md があるディレクトリに読み替える。

| ファイル | 使う場面 |
|---|---|
| `references/design-chapters.md` | 詳細設計書の章立てと技術選定の手順 |
| `references/requirement-exclusion.md` | 最小設計の意味、要件を外すときの手順、設計中に見つけた要件の不足の扱い |
| `references/design-completeness.md` | 設計書の網羅性チェック |
| `references/design-tasks-rules.md` | tasks.md の書き方 |
| `references/id-definitions.md` | 設計 ID の採番 |
| `references/trace-map-rules.md` | 対応表（コード設計章で触れる） |
| `references/document-rules.md` | 文書の書き方と、作成後のレビュー |
| `scripts/rq_ds_link_checker.py` | 要件 ID と設計 ID の対応チェック |

## 始める前に確かめること

- 外部連携がある場合: `isdd-external-research` の整合確認が終わり、未解消の不整合が無いこと。
- 既存コードがあるのに要件定義書も設計書も無い場合: このスキルではなく `isdd-reverse-engineering` を先に案内する（既存コードと食い違う設計を新しく作らないため）。

## 最小設計と要件の除外

`references/requirement-exclusion.md` に従う。要点は次のとおり。

- `docs/requirements.md` の要件（`RQ-BK`・`RQ-BZ`・`RQ-EF` を除く）はすべて設計に反映する。外すにはユーザーの承認が要り、承認された要件は設計書の「11-1. 除外要件」に書く。
- 要件定義書に無い設計要素は足さない。
- 設計中に要件 ID と設計 ID の未マッピングが出たら、1 件ずつユーザーに聞き直して `docs/requirements.md` を直し、設計に伝える。

## 技術選定

言語・フレームワーク・DB・実行形態に既定値は無い。`references/design-chapters.md` 第 1 章の手順で、要件定義書の「1-1. 技術制約」と要件を根拠に候補を比較して選ぶ。

- 候補ごとにインターネットで公式情報を調べ、出典 URL と確認日を比較表に書く。
- 検索・取得ツールが使えない環境では推測で選ばず、「インターネット調査ができないため技術選定を確定できない」と報告して止まる。ユーザーが情報を出すか、未調査のまま進める許可を出すまで他の章へ進まない。
- 選定結果をユーザーに示して承認を得る。承認の前に他の章へ進まない（技術が決まらないと他の章が書けないため）。

## 設計書の書き方

- 章立ては `references/design-chapters.md` に従う。第 11 章「要件と設計の対応表」（`DS-ID` と `対応要件ID` の 2 列で全設計 ID を 1 行ずつ並べる表）は、各章の表に対応要件 ID 列があっても置く。`rq_ds_link_checker.py` はこの表を対応の根拠に読むため。
- すべての設計要素に `references/id-definitions.md` に従って `DS-*` を付け、対応する `RQ-*` と結びつける。どの種類の設計 ID で受けるかは、同ファイルの「要件カテゴリと設計 ID の対応先」に従う（テストシナリオは `DS-TS`、運用は `DS-OP`、データは `DS-SC` など）。ID は表の専用列に書き、本文や図には書かない。
- 同じ意味の処理を 2 回作らず、共通化する前提で設計する。
- 冗長な設計要素を列挙し、要件を満たす範囲で削除する。
- 確認が要るのは、技術選定の承認と、要件レベルの不足（外部連携の API 仕様、外部スキーマなど）だけにする。それ以外はユーザーに確認せず進める。
- 文書の書き方は `references/document-rules.md` に従う。

設計・検証・修正を繰り返し、網羅性チェックとレビューが終わるまで続ける。

## 網羅性チェック

`references/design-completeness.md` の項目をすべて確認し、不足があれば直す。

## 保存と tasks.md

1. 設計書を `docs/detail_design.md` に保存する。
2. `.history/[YYYYMMDD]-[タスク名]/tasks.md` を `references/design-tasks-rules.md` に従って作る。「正本反映の確認タスク」は変更設計だけのものなので、このスキルでは入れない。

## 整合チェック

設計書ができたら、次を bash で実行する。

```bash
python3 .agents/skills/isdd-design/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md
```

チェッカーは、対応の無い要件 ID・設計 ID と、対応の矛盾を報告する（1 つの設計 ID が複数の要件 ID に対応するのは正常なので報告しない）。問題があれば終了コード 1 になる。

- 欠落・不整合があれば設計書を直して再実行する。
- 要件側の不足で未マッピングが出たら、`references/requirement-exclusion.md` の手順で `docs/requirements.md` を直し、ID の変更を設計書に伝えてから再実行する。
- 0 件になってからレビューへ進む。実行ログは応答に載せる。

## レビュー

`references/document-rules.md` のレビュー項目に加えて、次を確認する。問題があれば直してから報告する。

1. 冗長な設計が無いか
2. 網羅性チェックをすべて満たしているか
3. 承認の無い要件の除外が残っていないか

残課題がある場合はユーザーに示す。

## 次のステップ

完了を報告するときに、次のスキルを提案する。

- `scripts/isdd/check.sh` が無いプロジェクトでは、先に `isdd-setup` で対応表チェックを導入する
- `isdd-traceable-coding` で設計書にもとづく実装と対応表の作成を行う

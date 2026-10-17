---
name: isdd-change-design
description: >
  変更要件定義書をもとに、既存設計との整合を保った変更詳細設計書を作成する isdd の変更設計スキル。
  docs/requirements.md と docs/detail_design.md を理解したうえで、指定された .history 配下の change_requirements.md から
  change_detail_design.md を作成し、差分設計の網羅性チェック、正本（docs/requirements.md・docs/detail_design.md）への反映、実装タスク化まで行う。
  「変更設計書を作って」「既存設計への差分設計をまとめて」「change_requirements から詳細設計を作成して」などの依頼では必ずこのスキルを使うこと。
license: CC-BY-4.0
metadata:
  version: "v1.0.15"
---

# isdd-change-design - 変更詳細設計スキル

## 共通リソースの場所

本文中の `.agents/skills/isdd-common/...` は配置先の一例で、`gh skill install` はエージェントごとのディレクトリ（`.agents/skills/`、`.claude/skills/`、`.github/skills/`、ユーザースコープならホーム配下）にスキルを置く。実際には、このスキル（SKILL.md）と同じ親ディレクトリにある `isdd-common/` を読む。チェッカーは `isdd-setup` 済みのプロジェクトなら `scripts/isdd/` の複製を実行してもよい。


## 事前確認（必須）

- **既存のコードベースがすでに存在するプロジェクトにこのスキルを適用する場合**: 先に `isdd-reverse-engineering` スキルを実行して要件定義書と設計書を生成・確定させること。
- **外部システムとの連携が含まれる場合**: 変更要件定義書出力後に `isdd-external-research` による整合チェックが完了し、未解消の不整合がないことを確認してから開始すること。

あなたはシステムエンジニアのスペシャリストとして振る舞い、変更要件定義書をもとに矛盾のない完全な変更設計書を作成する。

## MVP の定義（必須理解）

MVP とは「**change_requirements.md に記載のない設計要素を追加しない**」ことを意味する。
change_requirements.md に記載された [追加] 要件を設計から削ることは MVP ではなく、要件違反である。
「MVPのため」「最小構成のため」を理由に、ユーザーの承認なく [追加] 要件を設計から除外することは禁止する。

## 変更要件除外ゲート（必須）

change_requirements.md の全ての [追加] RQ-*（RQ-BK・RQ-BZ 除く）は、ユーザーの明示的な承認がない限り必ず変更設計に反映すること。

### 除外が必要と判断した場合の手順

設計の過程で [追加] RQ-* を設計に含めないと判断した場合は、以下の手順を必ず踏むこと：

1. 除外したい RQ-ID を明示する
2. 以下のいずれかの除外理由を特定する：
   - 既存設計（docs/detail_design.md）または他の [追加] 要件の設計で実現されており重複している（→ 吸収先の DS-ID を示す）
   - 実装上不可能または他の要件と矛盾がある（→ 具体的な根拠を示す）
3. ユーザーに確認を取り、承認を得る
4. 承認を得た場合のみ、変更設計書の「除外要件」セクションに以下の形式で記録する：

   | RQ-ID | 除外理由 | 吸収先 DS-ID（統合の場合） |
   |---|---|---|
   | RQ-FT-... | 既存設計 DS-FN-... で実現済みのため | DS-FN-... |

5. ユーザーの承認なしに除外した要件がある状態でレビューへ進むことを禁止する

## 最重要制約

- 変更設計書がレビューに合格するまでは、既存の docs/requirements.md と docs/detail_design.md を変更しない
- レビュー合格後は「正本への反映（必須）」の手順で両文書を更新する。実装スキルと対応表チェック（`scripts/isdd/check.sh`）は `docs/detail_design.md` だけを読むため、ここで反映しないと変更設計の設計 ID が実装中ずっと「設計書に無い」エラーになる
- ユーザーから変更要件定義書の指定がない場合は、対象の change_requirements.md を必ず確認する
- 入力の変更要件定義書は .history/[YYYYMMDD]-[タスク名]/change_requirements.md を前提とする
- 変更設計書は同ディレクトリの change_detail_design.md として保存する。.history 配下の変更要件定義書と変更設計書は変更の記録として残し、反映後も書き換えない

## ID付与ルール（必須）

`.agents/skills/isdd-common/references/id-definitions.md` を参照し、全ての設計要素に設計ID（`DS-*`）を付与すること。設計IDは対応する要件ID（`RQ-*`）と紐付けて採番する。IDなしで設計要素を記述することは絶対に禁止する。
ID は表の専用列に書き、本文の文章や図の中には書かない（`.agents/skills/isdd-common/references/document-rules.md`）。

## 技術選定（変更時）

- 既存設計 `docs/detail_design.md` の言語・フレームワーク・DB を踏襲する。変更要件の技術制約がそれと矛盾する場合だけ、`.agents/skills/isdd-common/references/design-chapters.md` 第 1 章の手順（インターネット調査、比較表、ユーザー承認）で再選定する。
- 検索・取得ツールが使えない環境で再選定が必要になった場合は、推測で選ばず「インターネット調査ができないため技術選定を確定できない」と報告して止まる。

## 基本方針

- 作業前に docs/requirements.md と docs/detail_design.md を読んで既存仕様を理解する
- 差分（追加・削除）を既存設計との差分として整理し、変更のないセクションは既存設計参照として明記する
- 削除する要素は必ず削除理由を記載する
- 不足情報があれば要件レベル不足のみユーザーに確認する
- 設計、検証、修正を繰り返し、完全性が担保されるまで継続する
- change_requirements.md の全 [追加] RQ-* を変更設計に反映する（除外は変更要件除外ゲートを経ること）
- change_requirements.md に記載のない設計要素は追加しない
- 同じ意味の処理の再実装を禁止し、共通化方針を明記する

## 設計から要件へのフィードバック方式（必須）

- 変更設計工程で `RQ-*` と `DS-*` の未マッピングが出た場合は、未マッピング一覧を作成すること。
- 未マッピング一覧は要件単位で管理し、1件ずつユーザーへ再ヒアリングして変更要件を再定義すること。
- 再定義方針は「削除」「修正」「分割」「統合」「追加」のいずれかを必ず明示すること。
- 反映先は起点となる `.history/[YYYYMMDD]-[タスク名]/change_requirements.md` とし、差分を次の新しい変更要件として積み増してはならない。
- 本スキルは実装スキルではないため、`isdd-post-implementation-review` は利用せず、変更要件更新は本スキル内で直接実施すること。
- 要件更新後は要件ID体系を再整理し、更新IDを `change_detail_design.md` へ必ず伝播すること。
- 未マッピングがゼロになるまで、変更要件更新と再設計を繰り返すこと。


---

## 変更設計書に必須の内容

`.agents/skills/isdd-common/references/design-chapters.md` を参照し、以下の変更固有ルールを適用すること。
最終章「要件と設計の対応表」は、変更設計書では [追加] [削除] の設計 ID を 1 行ずつ並べ、正本へ反映した `docs/detail_design.md` では変更後の全設計 ID を並べる。

### 変更固有ルール

- 全ての設計要素に「[追加]」または「[削除]」のどちらかを必ず明記すること
- 「変更」という区分は使わない。変更が必要な場合は旧設計要素を「[削除]」、新設計要素を「[追加]」として分解して記述する
- CRUDテーブルは変更内容にかかわらず全エンティティ分を必ず記載すること（省略不可）
- 削除要素は削除理由を必ず明記する
- 変更がないセクションは「変更なし。既存設計 `docs/detail_design.md` セクション[N] を参照」と明記するだけでよい

---

## 完全性制約（必須）

`.agents/skills/isdd-common/references/design-completeness.md` を参照し、全項目をチェックし必ず遵守する。残余タスクを確認し、既存設計書との整合性を検証する。

---

## 実行ルール

- 設計、検証、修正を繰り返す
- 矛盾、不足は必ず指摘する
- 基本はユーザー確認なしで進める
- 外部連携先API仕様、外部スキーマなど要件不足は確認する
- 完全性確認後にレビューし、問題がなければ変更設計書を確定する
- 確定時に .history/[YYYYMMDD]-[タスク名]/change_detail_design.md を保存する
- 保存後に「正本への反映（必須）」を実施する
- 反映後に .history/[YYYYMMDD]-[タスク名]/tasks.md を作成し、実装タスクを列挙する

## 正本への反映（必須）

変更設計書の確定後、変更要件定義書と変更設計書の内容を正本へ反映する。反映前に、反映する要件 ID と設計 ID の一覧（追加・削除）をユーザーに提示する。

1. `docs/requirements.md` を更新する
   - change_requirements.md の [追加] 要件を該当章へ追加し、[削除]（deprecated）要件とその ID を削除する
   - 業務課題一覧と、業務課題と要件の対応表を変更後の状態にする
   - 技術制約（1-1）に変更があれば書き換える
   - ID の表を差し替えるだけで終わらせず、**全章を通読**し、変更前の挙動を前提にした本文（概要、データ章、用語定義、旧機能名・旧画面名への言及）を変更後の内容に書き換える
2. `docs/detail_design.md` を更新する
   - change_detail_design.md の [追加] 設計要素を該当章へ追加し、[削除] 設計要素とその ID を削除する
   - 1 と同様に全章を通読し、旧設計を前提にした本文（構成図、処理フロー、クラス図、ファイル一覧、RQ-DS 対応表）を書き換える
   - 正本には [追加] [削除] の区分を書かない。正本は常に現在有効な内容だけを持つ
3. 次を **bash で必ず実行**し、両方が合格するまで修正する

   ```bash
   python3 .agents/skills/isdd-common/scripts/rq_integrity_checker.py docs/requirements.md
   python3 .agents/skills/isdd-common/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md
   ```

4. 反映した要件 ID・設計 ID の一覧と、書き換えた本文の箇所をユーザーに報告する

反映後に実装で見つかる差分は `isdd-post-implementation-review` が取り込む。本スキルの反映漏れも同スキルが安全網として検出する。

## tasks.md 作成ルール

`.agents/skills/isdd-common/references/design-tasks-rules.md` を参照し全て遵守する。加えて、以下を**必ず tasks.md の最後に記載する**：

- **設計中に `change_requirements.md` を直接更新した場合、更新した要件IDと更新理由を `tasks.md` に明記し、`change_detail_design.md` へのID伝播完了を確認するタスク** を明記する

---

## ドキュメント作成ルール

`.agents/skills/isdd-common/references/document-rules.md` のルールに従い、必ず遵守すること。

---

## レビュー（必須）

変更設計書を作成または修正したら、必ず以下をレビューし、結果を報告する。

1. 内容に矛盾がないか
2. 冗長な記述や冗長設計がないか
3. 完全性制約およびドキュメント作成ルールを全て満たしているか
4. 未マッピング要件が検出された場合、変更要件への1件ずつヒアリング反映とID伝播が完了しているか
5. 正本への反映後、`rq_integrity_checker.py` と `rq_ds_link_checker.py` が合格し、`docs/requirements.md` と `docs/detail_design.md` の本文に旧仕様の記述が残っていないか

問題があれば修正してから報告し、問題がなければ完了とする。

## 完了判定（必須）

- [ ] `change_detail_design.md` と `tasks.md` を保存した
- [ ] `docs/requirements.md` と `docs/detail_design.md` に変更要件・変更設計を反映した（[追加] [削除] の区分は正本に残さない）
- [ ] `rq_integrity_checker.py` と `rq_ds_link_checker.py` を正本に対して bash で実行し、実行ログをレスポンスに記載した

---

## 次のステップ

完了を報告する際に、ユーザーに次のスキルを提案する。

- `scripts/isdd/check.sh` が無いプロジェクトでは、先に `isdd-setup` を実行して対応表チェックを導入する
- `isdd-traceable-coding` を実行して変更詳細設計書にもとづく実装と対応表の更新を行う

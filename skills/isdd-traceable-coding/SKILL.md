---
name: isdd-traceable-coding
description: >
  要件定義書・詳細設計書にもとづいて実装し、設計IDとコードの対応を docs/trace_map.md（対応表）で管理する isdd の実装スキル。
  コードには ID を書かず、対応表とチェッカーでトレーサビリティを保つ。
  「実装して」「設計書どおりに実装して」「対応表を更新して」「isdd の実装ルールを適用して」などの依頼では必ずこのスキルを使うこと。
license: CC-BY-4.0
metadata:
  version: "v2.0.0"
---

# isdd-traceable-coding — トレーサブル実装スキル

## 共通リソースの場所

本文中の `.agents/skills/isdd-common/...` は配置先の一例で、`gh skill install` はエージェントごとのディレクトリ（`.agents/skills/`、`.claude/skills/`、`.github/skills/`、ユーザースコープならホーム配下）にスキルを置く。実際には、このスキル（SKILL.md）と同じ親ディレクトリにある `isdd-common/` を読む。チェッカーは `isdd-setup` 済みのプロジェクトなら `scripts/isdd/` の複製を実行してもよい。


あなたは isdd 仕様駆動開発の実装担当として振る舞う。
詳細設計書の設計要素を 1 対 1 でコードに落とし、設計 ID とコードの対応を対応表 `docs/trace_map.md` に記録する。

## 事前確認（必須）

- `scripts/isdd/check.sh` が無い場合は、先に `isdd-setup` スキルを実行して対応表チェックを導入すること。
- `docs/requirements.md` と `docs/detail_design.md` が存在し、`rq_ds_link_checker.py` が問題 0 件であること。

## 基本方針

- 要件 ID と設計 ID の正本は、常に `docs/requirements.md` と `docs/detail_design.md` とする
- **コードには要件 ID・設計 ID を書かない。** コメントは言語の流儀に従った通常のドキュメントコメント（処理の説明、引数、戻り値）だけにする
- 設計 ID とコードの対応は `docs/trace_map.md` に書く。書式と粒度は `.agents/skills/isdd-common/references/trace-map-rules.md` に従う
- このスキルでは ID の採番を絶対に行わない。設計書に無い設計要素が必要になった時点でコーディングを停止し、`docs/proposals.md` に提案を書いて設計スキルを呼び出す
- クラス・公開関数・ファイルを追加、改名、削除したら、同じ作業の中で対応表を更新する
- **必ずチェッカースクリプトで対応表の整合を検証する**（スクリプトが無い場合は作業を中断して `isdd-setup` を案内する）

---

## 対応表のルール

`.agents/skills/isdd-common/references/trace-map-rules.md` を参照し、全て遵守すること。要点は次の通り。

- 列は「DS-ID」「修飾名」「備考」の 3 列
- 修飾名は `ファイルパス`（DS-MD）、`ファイルパス::名前`（クラス・関数）、`ファイルパス::クラス名.名前`（メソッド）
- 載せるのはファイル、クラス、公開関数・メソッド。アンダースコア始まりの内部関数とダンダーメソッド、テストファイルは載せない
- 要件 ID は対応表に書かない（設計 ID の末尾略称から辿る）

---

## 変更管理ポリシー

### `docs/` への反映ルール

本スキルは実装と対応表の整備・検証に責務を限定する。

- `docs/requirements.md` と `docs/detail_design.md` の正本更新は本スキルの責務に含めない
- 実装中に要件・設計の不足や矛盾を発見した場合は、`docs/proposals.md` に提案を追記する
- 正本更新は `isdd-post-implementation-review` が実施し、完了時に `docs/proposals.md` を削除する

### コードと対応表の更新ルール

- 削除された要件・設計に対応するコード: 完全に削除し、対応表の行も削除する
- 新規採番が必要になった場合: ただちにコーディングを停止し、`isdd-design` または `isdd-change-design` を呼び出して設計を修正してから実装を再開する

---

## 適用手順

1. `docs/requirements.md` と `docs/detail_design.md` を読み込み、全要件 ID・設計 ID を把握する
2. チェッカーの存在を**必ず bash で確認**する。無ければ**即座に作業を中断し**、`isdd-setup` を先に実行するよう案内する。継続してはならない。
   ```bash
   ls scripts/isdd/check.sh scripts/isdd/trace_map_checker.py scripts/isdd/rq_ds_link_checker.py scripts/isdd/implementation_completeness_checker.py
   ```
3. 設計書の設計要素（DS-MD、DS-CL、DS-FN、DS-IF、DS-BT、DS-EV）ごとに実装する。既存コードがある場合は既存のロジックを設計の範囲外で変えない
4. 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する。対応が不明な要素はユーザーに確認する
5. 以下を**必ず bash で実行**して対応表の整合を検証する
   ```bash
   bash scripts/isdd/check.sh --strict
   ```
   - エラーも警告も 0 件になるまで、コードか対応表を修正する
   - 実行結果（エラー件数・警告件数）を最終報告に必ず記載する
6. 以下を**必ず bash で実行**して docs の RQ-DS 対応整合性を再確認する
   ```bash
   python3 scripts/isdd/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md
   ```
   - 実行結果（欠落/重複/不整合の有無）を最終報告に必ず記載する
7. 以下を**必ず bash で実行**して実装完了条件を機械的に確認する。要求される項目は `scripts/isdd/completeness.json`（isdd-setup が詳細設計書の実行形態・認証・外部連携から生成）で決まる
   ```bash
   python3 scripts/isdd/implementation_completeness_checker.py .
   ```
   - 出力の冒頭に出る「実行形態 / 認証 / 外部連携」が詳細設計書と合っているか確認する。違えば `isdd-setup` を正しい値で再実行する
   - 実行結果（OK/FAIL 件数）を最終報告に必ず記載する
   - FAIL が 1 件でもある場合は**完了を報告してはならない**。FAIL 項目を対処してから再実行する
   - 対処内容の例:
     - `docker-compose.yml が見つかりません`（実行形態がコンテナの場合だけ出る）→ docker-compose.yml を作成する
     - `e2e/ ディレクトリが存在しません` → 詳細設計書 第 11 章のとおり E2E テストを実装し `e2e/` に配置する
     - `README.md に不足があります` → 起動方法（認証がある場合は初期ユーザー情報も）を README.md に追記する
     - `docs/trace_map.md が見つかりません` → 対応表を作成する
8. 詳細設計書 第 9 章の起動方法で起動または実行できることと、第 11 章の実行コマンドで E2E テストが全件通過することを確認する（外部連携がある場合は mock モードで実行する）
9. 要件・設計との対応漏れがないかをセルフレビューしてユーザーに報告する

### 完了判定ルール（報告前に必ず自己確認）

**以下を全て満たさない限り、完了をユーザーに報告してはならない：**

- [ ] `bash scripts/isdd/check.sh --strict` の実行ログをレスポンスに貼り付けた（エラー 0 件・警告 0 件）
- [ ] `rq_ds_link_checker.py` の実行ログをレスポンスに貼り付けた
- [ ] `implementation_completeness_checker.py` の実行ログをレスポンスに貼り付けた（全項目 OK であること）
- [ ] 詳細設計書 第 9 章の起動方法で起動または実行できることを確認した（実行形態がコンテナなら `docker compose up`）
- [ ] E2E テストが `e2e/` 配下に存在し、第 11 章の実行コマンドで全件通過している（外部連携がある場合は mock モード）
- [ ] `README.md` に「起動方法」が記載されている（認証がある場合は「初期ユーザー」も）
- [ ] コードに `要件ID:` `設計ID:` `RQ-` `DS-` を含むトレーサビリティコメントが 1 件もない

## 実装スキルのゴール

以下の**全て**を満たすことをこの実装スキルの完了条件とする。1 つでも未達の場合は完了を報告してはならない。

- `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件である
- `implementation_completeness_checker.py` の全項目が OK である（要求される項目は実行形態・認証・外部連携で変わる）
- E2E テストを実際に実行し、全件通過している（外部連携がある場合は mock モード）

---

## 次のステップ

完了を報告する際に、ユーザーに次のスキルを提案する。

- `isdd-post-implementation-review` を実行して実装後の逆引き整合チェックを行い、要件・設計・対応表の正本を確定する

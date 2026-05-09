# 対話駆動仕様開発 - 要件・設計・ソースをIDで一貫追跡する

isdd（Interview-driven Spec-driven Development）はインタビュー駆動で仕様を確定して、要件・設計・ソースをIDで一貫追跡しながら、開発を進める手法です。

スキル群は `skills/` に格納し、`gh skill publish` で GitHub に公開・`gh skill install` で導入する形式で管理します。

## 背景と目的

isdd は、AI 実装で起こりやすい次の問題を抑制することを目的とします。

1. 要件の曖昧さによる意図しない実装差分
2. 変更時の影響範囲不明による品質低下
3. 仕様とコードの対応関係が失われることによる保守性低下

そのため、isdd では要件と設計を先に確定し、実装では要件 ID と設計 ID を基準にトレーサビリティを維持します。

## かんたんな使い方

### 全スキルの最新版を導入する

最初の導入は対話モードで実行し、スキル選択画面で `(all skills)` を選ぶ。

```bash
gh skill install notfolder/req-spec-driven
```

`@vX.Y.Z` を付けずにインストールすると、公開されている最新リリースが導入される。

### 要件定義の起動方法

導入後は、エージェントの入力で次のように開始する。

```text
/isdd-requirements [XXXアプリを作りたい]
```

---

## 開発フロー全体像

### 新規開発フロー

```mermaid
graph TD
    G1[開始ゲート\n業務課題確定・外部連携有無・既存コード有無を確認]
    PRE[isdd-external-precheck\n外部連携事前確認]
    REV[isdd-reverse-engineering\n既存プロジェクトの仕様化]
    REQ[isdd-requirements\n要件定義]
    EX[isdd-external-research\n外部仕様整合確認]
    DES[isdd-design\n詳細設計]
    COD[isdd-traceable-coding\n実装]

    G1 -->|外部連携あり| PRE
    G1 -->|外部連携なし| REQ
    G1 -->|既存コードあり かつ isdd未導入| REV
    PRE --> REQ
    REV --> REQ
    REQ -->|外部連携あり| EX
    REQ -->|外部連携なし| DES
    EX --> DES
    DES --> COD
```

### 変更フロー

```mermaid
graph TD
    G2[開始ゲート\n業務課題と外部連携有無を確認]
    PRE[isdd-external-precheck\n外部連携事前確認]
    CREQ[isdd-change-req\n変更要件定義]
    EX[isdd-external-research\n外部仕様整合確認]
    CDES[isdd-change-design\n変更詳細設計]
    COD[isdd-traceable-coding\n実装]

    G2 -->|外部連携あり| PRE
    G2 -->|外部連携なし| CREQ
    PRE --> CREQ
    CREQ -->|外部連携あり| EX
    CREQ -->|外部連携なし| CDES
    EX --> CDES
    CDES --> COD
```

### 既存プロジェクト適用フロー

```mermaid
graph TD
    A[コード構造解析]
    B[要件定義書の逆引き生成]
    C[詳細設計書の逆引き生成]
    D[インタビュー補完]
    E[ID採番と整合確認]
    F[トレーサブルコメント適用]
    G[自己検証と報告]

    A --> B --> C --> D --> E --> F --> G
```

---

## スキル一覧

| スキル名 | 役割 | 主な成果物 |
|---|---|---|
| isdd-requirements | インタビュー駆動で要件定義書を作成する | docs/requirements.md |
| isdd-design | 要件定義書から詳細設計書と実装タスクを作成する | docs/detail_design.md、.history/[日付]-[タスク名]/tasks.md |
| isdd-change-req | 既存要件に対する変更要件定義書を作成する | .history 配下の change_requirements.md |
| isdd-change-design | 変更要件から変更詳細設計書と実装タスクを作成する | .history/[日付]-[タスク名]/change_detail_design.md、.history/[日付]-[タスク名]/tasks.md |
| isdd-external-precheck | 外部連携の接続可否・認証方式・主要制限を事前確認する | precheck_report.md |
| isdd-external-research | 外部連携先の詳細仕様を調査し要件との整合を確認する | alignment_report.md、external 配下調査成果物 |
| isdd-reverse-engineering | 既存コードから要件・設計を逆引きし isdd 化する | docs/requirements.md、docs/detail_design.md |
| isdd-traceable-coding | 要件 ID と設計 ID に基づく実装コメント規則を適用する | 各ソースファイルのトレーサブルコメント |
| isdd-common | 共通参照ルールを提供する基盤スキル | skills/isdd-common/references 配下の定義ファイル |

---

## サブエージェント一覧

| エージェント名 | 主な利用スキル | 役割 |
|---|---|---|
| code-structure-analyzer | isdd-reverse-engineering | 既存コードの構造解析を分離実行する |
| external-research-investigator | isdd-external-research | 外部ライブラリ候補の調査と評価を実行する |
| db-schema-extractor | isdd-external-research | 外部 DB スキーマ情報の抽出を実行する |

---

## 共通リファレンスとスクリプト

isdd-common の references 配下に全スキルで参照する共通ルール、scripts 配下に整合性検証スクリプトを格納します。

### references/

| ファイル | 内容 |
|---|---|
| id-definitions.md | 要件 ID と設計 ID の定義 |
| document-rules.md | 仕様書・設計書の記述ルール |
| requirements-chapters.md | 要件定義書の章構成 |
| design-chapters.md | 詳細設計書の章構成 |
| design-completeness.md | 設計網羅性の確認ルール |
| design-tasks-rules.md | 実装タスク化のルール |
| hearing-complexity-rules.md | ヒアリング共通ルール |

### scripts/

| スクリプト | 用途 | 実行例 |
| --- | --- | --- |
| rq_integrity_checker.py | 要件定義書の RQ-* 内部整合性を検証（BKマッピング・フォーマット） | `python3 rq_integrity_checker.py docs/requirements.md` |
| rq_ds_link_checker.py | 要件ID（RQ-*）と設計ID（DS-*）の対応欠落・重複・不整合を検証 | `python3 rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` |
| trace_comment_coverage_checker.py | ソースコードのトレーサブルコメント付与率と記載不足を検証 | `python3 trace_comment_coverage_checker.py src/` |

---

## バージョン管理

各スキルは SKILL.md の frontmatter に metadata.version を持ち、同一リリースでは全スキルのバージョンを揃えて管理します。

---

## GitHub Skill 公開手順

スキルの編集は `skills/` 配下で直接行い、`gh skill publish` で GitHub に公開します。

### 事前確認

1. `skills/` 配下の各 SKILL.md の frontmatter に `license` フィールドが含まれていることを確認する。
2. 公開前に dry-run を実行し、エラーがないことを確認する。

### dry-run（検証のみ）

```bash
gh skill publish ./skills --dry-run
```

### 本番公開

```bash
gh skill publish ./skills --tag v1.0.12
```

---

## スキル導入手順（gh skill install）

公開済みスキルは `gh skill install` で導入する。

### 全スキルを導入

```bash
gh skill install notfolder/req-spec-driven
```

### 1つのスキルを導入

```bash
gh skill install notfolder/req-spec-driven isdd-requirements
```

### バージョンを固定して導入

```bash
gh skill install notfolder/req-spec-driven isdd-requirements@v1.0.12
```

### ユーザースコープへ導入

```bash
gh skill install notfolder/req-spec-driven isdd-requirements --scope user
```

必要に応じて skill 名を isdd-design など他のスキル名に置き換えて導入する。

---

## Waza 評価運用

評価資材は `evals/[skill-name]/` 配下に配置し、評価は `evals/run-all.sh` で実行する。`waza run --discover` は使用しない。

### 特定スキルのみ実行

```bash
bash evals/run-all.sh real isdd-change-design
bash evals/run-all.sh real isdd-requirements isdd-design
```

### 全スキル一括実行

```bash
bash evals/run-all.sh real
```

### mock モードについて

`eval.mock.yaml` が存在するスキルのみ mock モードで実行できる。

```bash
bash evals/run-all.sh mock
```

### 単体実行（デバッグ用）

```bash
waza run evals/[skill-name]/eval.copilot.yaml --context-dir evals/[skill-name]/fixtures -v
```

---

---
name: isdd-common
description: >
  isdd スキル群が共有する参照ファイル群。他のスキルから references/ 配下のファイルを読み込むための共通リソース。
  単独で起動されることはなく、isdd-requirements / isdd-design などのスキルから参照される。
license: CC-BY-4.0
metadata:
  version: "v2.0.0"
---

# isdd-common

isdd スキル群の共通参照ファイルを提供するリソースパッケージ。

## 配置先について

他のスキルの本文では、ここにあるファイルを `.agents/skills/isdd-common/...` と書いている。これは配置先の一例で、`gh skill install` はエージェントごとのディレクトリ（`.agents/skills/`、`.claude/skills/`、`.github/skills/`、ユーザースコープならホーム配下）に置く。各スキルは、自分の SKILL.md と同じ親ディレクトリにある `isdd-common/` を実際の場所として読み替える。チェッカーは、`isdd-setup` 済みのプロジェクトなら `scripts/isdd/` の複製を実行してもよい。

## 内容

- `references/document-rules.md` — 仕様書・設計書の記述ルール
- `references/hearing-complexity-rules.md` — ヒアリング共通ルール
- `references/id-definitions.md` — 要件ID・設計IDの定義
- `references/requirements-chapters.md` — 要件定義書の章構成
- `references/design-chapters.md` — 詳細設計書の章構成
- `references/design-completeness.md` — 設計網羅性チェックリスト
- `references/design-tasks-rules.md` — 実装タスク化のルール
- `references/trace-map-rules.md` — 設計IDとコードの対応表（docs/trace_map.md）の書式・粒度・チェック規則
- `scripts/rq_integrity_checker.py` — 要件定義書の RQ-* 内部整合性を検証
- `scripts/rq_ds_link_checker.py` — 要件ID（RQ-*）と設計ID（DS-*）の対応欠落・不整合を検証
- `scripts/trace_map_checker.py` — 詳細設計書・対応表・コードの 3 者を突合し、壊れた参照（エラー）と未登録（警告）を検出。Python・TypeScript / JavaScript・Java・Go は記号まで、その他の言語はファイルの存在だけ確認する
- `scripts/implementation_completeness_checker.py` — E2E テスト・README.md の起動方法・docs/trace_map.md の存在を機械確認。docker compose と「初期ユーザー」は scripts/isdd/completeness.json の実行形態・認証に応じて要求する
- `scripts/isdd_setup.py` — チェッカーを scripts/isdd/ に複製し、check.sh・pre-commit・completeness.json を生成し、AGENTS.md と CLAUDE.md に規則を追記する（isdd-setup スキルが実行）

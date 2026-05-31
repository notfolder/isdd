---
name: isdd-common
description: >
  isdd スキル群が共有する参照ファイル群。他のスキルから references/ 配下のファイルを読み込むための共通リソース。
  単独で起動されることはなく、isdd-requirements / isdd-design などのスキルから参照される。
license: CC-BY-4.0
metadata:
  version: "v1.0.13"
---

# isdd-common

isdd スキル群の共通参照ファイルを提供するリソースパッケージ。

- `references/document-rules.md` — 仕様書・設計書の記述ルール
- `references/hearing-complexity-rules.md` — ヒアリング共通ルール
- `references/id-definitions.md` — 要件ID・設計IDの定義
- `references/requirements-chapters.md` — 要件定義書の章構成
- `references/design-chapters.md` — 詳細設計書の章構成
- `references/design-completeness.md` — 設計網羅性チェックリスト
- `references/design-tasks-rules.md` — 実装タスク化のルール
- `scripts/rq_ds_link_checker.py` — 要件ID（RQ-*）と設計ID（DS-*）の対応欠落・重複・不整合を検証
- `scripts/trace_comment_coverage_checker.py` — ソースコードのトレーサブルコメント付与率と記載不足を検証
- `scripts/implementation_completeness_checker.py` — docker-compose.yml の存在・e2e/ 配下のテストファイル存在・README.md の起動方法/初期ユーザー記載を機械確認

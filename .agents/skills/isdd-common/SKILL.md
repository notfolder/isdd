---
name: isdd-common
description: >
  isdd スキル群が共有する参照ファイル群。他のスキルから references/ 配下のファイルを読み込むための共通リソース。
  単独で起動されることはなく、isdd-requirements / isdd-design などのスキルから参照される。
metadata:
  version: "1.0.9"
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

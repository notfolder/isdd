# CLAUDE

<!-- isdd-setup:begin -->
## isdd トレーサビリティ規則（isdd-setup が管理する。手で編集しない）

- 仕様とコードの対応は `docs/trace_map.md`（対応表）で管理する。コードに要件 ID や設計 ID を書かない。
- クラス・公開関数・ソースファイルを追加、改名、削除したら、同じ作業の中で `docs/trace_map.md` の行を更新する。E2E テストは `DS-TS-*` の行でテスト関数に結ぶ。
- コードを変更した作業の終わりに `bash scripts/isdd/check.sh` を実行する（対応表と、`scripts/isdd/dependencies.json` の依存の規則を確かめる）。エラーが出たら直してから作業を終える。警告は報告に含める。
- 設計要素を増やす必要があれば、コードを書く前に `docs/detail_design.md` を更新する。設計 ID の採番は `isdd-spec` の責務で、実装中に ID を作らない。
- `docs/active_change` がある間は変更の実装中。そこに書かれた変更のディレクトリの変更要件定義書・変更設計書を正本に重ねて読む。正本への反映は実装後に `isdd-build` の実装後レビューが行う。
<!-- isdd-setup:end -->

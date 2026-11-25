# tasks.md（不具合修正: 空行が余分に出る）

0. isdd-setup 導入確認タスク
   - `scripts/isdd/check.sh` が無い、または `scripts/isdd/VERSION` がスキルの版と違えば `isdd-setup` を実行する
   - 完了条件: `bash scripts/isdd/check.sh` が実行できる

0-2. 進行中の変更の登録確認タスク
   - `docs/active_change` の 1 行目が `.history/20260601-fix-blank-line/` を指していることを確認する。正本には反映しない
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行がある（原因がコードなので、変更設計書との組み合わせのチェックは行わない）

0-3. 再現するテストのタスク
   - `bug_report.md` の「再現するテスト」を `e2e/` に書き、直す前に実行して落ちることを確かめる。対応表の `DS-TS-HELLO-OUTPUT-E2E-TS-VERIFY-HELLO-WORLD-OUTPUT` の行にテスト関数を足す
   - 完了条件: 直す前の実行でそのテストが失敗する

1. `src/hello.py` の `print_hello_world` を設計書どおりに直す（実装する設計 ID: `DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD`）
   - 完了条件: E2E が全件通り、`bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件

2. すべての変更点を実装したかを確認する

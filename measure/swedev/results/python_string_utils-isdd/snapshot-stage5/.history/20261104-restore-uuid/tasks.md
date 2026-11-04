# タスク: UUID の判定（is_uuid）と生成（uuid）の実装し直し

変更要件定義書と変更設計書にもとづく。上から順に実行する。

## 0. 実装開始前の固定タスク

### 0. isdd-setup 導入確認タスク

- 対象の設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が存在し、`scripts/isdd/completeness.json` の実行形態（library）・認証（なし）・外部連携（なし）が詳細設計書と一致していることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- 対象の設計 ID: なし（登録の確認）
- 内容: `docs/active_change` の 1 行目が `.history/20261104-restore-uuid/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない。反映は実装後に `isdd-build` の実装後レビューが行う。
- 完了条件: `docs/active_change` の指す先が正しいこと。

## 1. 実装タスク

### 1. UUID 判定関数の実装

- 対象の設計 ID: `DS-FN-IS-UUID`
- 内容: `string_utils/validation.py` に `is_uuid(input_string: Any, allow_hex: bool=False) -> bool` を実装する（変更設計書 4-2 の仕様どおり。`UUID_RE` と `UUID_HEX_OK_RE` を使う）。
- 完了条件: 標準表記の UUID は真。ハイフンなしは `allow_hex=True` のときだけ真。非文字列は文字列に変換して判定し、誤った値は偽。

### 2. UUID 生成関数の実装

- 対象の設計 ID: `DS-FN-UUID`
- 内容: `string_utils/generation.py` に `uuid(as_hex: bool=False) -> str` を実装する（`uuid4()` を使う。`as_hex` で 16 進かどうかを切り替える）。
- 完了条件: 既定は 8-4-4-4-12 のハイフン区切り、`as_hex=True` は 32 桁の 16 進を返す。生成した値は `is_uuid` で真になる。

### 3. 単体テスト・結合テスト全件通過タスク

- 対象の設計 ID: `DS-FN-IS-UUID`、`DS-FN-UUID`、既存の全関数
- 内容: 作業ディレクトリの `.venv` で `python -m pytest tests` を実行する。
- 完了条件: FAIL と ERROR が 0 件。

### 4. E2E テストの実行

- 対象の設計 ID: `DS-TS-VERIFY-VALIDATION-BASICS`、`DS-TS-VERIFY-GENERATION`
- 内容: `python -m pytest e2e --junitxml=e2e/results/e2e.xml` を実行する。
- 完了条件: FAIL と ERROR が 0 件。

### 5. 対応表（docs/trace_map.md）の確認

- 対象の設計 ID: `DS-FN-IS-UUID`、`DS-FN-UUID`
- 内容: 既存の行が `string_utils/validation.py::is_uuid`、`string_utils/generation.py::uuid` を指していることを確かめる（行は既にある）。
- 完了条件: `bash scripts/isdd/check.sh` がエラー 0 件。

### 6. 実装後レビュー

- 内容: `isdd-build` の実装後レビューで変更を正本へ反映する（正本の内容は既に一致しているため、確認と `docs/active_change` の削除）。

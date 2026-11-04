# タスク: 空でない文字列の判定と IPv4 判定関数の実装し直し

変更要件定義書と変更設計書にもとづく。上から順に実行する。

## 0. 実装開始前の固定タスク

### 0. isdd-setup 導入確認タスク

- 対象の設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が存在し、`scripts/isdd/completeness.json` の実行形態（library）・認証（なし）・外部連携（なし）が詳細設計書と一致していることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- 対象の設計 ID: なし（登録の確認）
- 内容: `docs/active_change` の 1 行目が `.history/20261104-restore-full-string-and-ip-v4/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない。反映は実装後に `isdd-build` の実装後レビューが行う。
- 完了条件: `docs/active_change` の指す先が正しいこと。

## 1. 実装タスク

### 1. 空でない文字列の判定関数の実装

- 対象の設計 ID: `DS-FN-IS-FULL-STRING`
- 内容: `string_utils/validation.py` に `is_full_string(input_string: Any) -> bool` を実装する（正本の `docs/detail_design.md` の仕様どおり。`is_string` で型を確かめ、空白を除いて空でないかを返す）。
- 完了条件: 文字列以外・空・空白だけで偽、それ以外で真を返すこと。

### 2. IPv4 判定関数の実装

- 対象の設計 ID: `DS-FN-IS-IP-V4`
- 内容: `string_utils/validation.py` に `is_ip_v4(input_string: Any) -> bool` を実装する（`is_full_string` で確かめ、`SHALLOW_IP_V4_RE` で形式を確かめ、各区切りが 0〜255 か確かめる）。
- 完了条件: 正しい IPv4 は真、範囲外・形式外・空白入りは偽。

### 3. 単体テスト・結合テスト全件通過タスク

- 対象の設計 ID: `DS-FN-IS-FULL-STRING`、`DS-FN-IS-IP-V4`、既存の全関数
- 内容: `python -m pytest tests` を実行する（作業ディレクトリの .venv を使う）。
- 完了条件: FAIL と ERROR が 0 件。

### 4. E2E テストの実行

- 対象の設計 ID: `DS-TS-VERIFY-VALIDATION-BASICS`、`DS-TS-VERIFY-PUBLIC-API-IMPORT`
- 内容: 既存の `e2e/test_scenarios.py` を `python -m pytest e2e --junitxml=e2e/results/e2e.xml` で実行する。
- 完了条件: FAIL と ERROR が 0 件。

### 5. 対応表（docs/trace_map.md）の確認

- 対象の設計 ID: `DS-FN-IS-FULL-STRING`、`DS-FN-IS-IP-V4`
- 内容: 既存の行が `string_utils/validation.py::is_full_string`、`::is_ip_v4` を指していることを確かめる（行は既にある）。
- 完了条件: `bash scripts/isdd/check.sh` がエラー 0 件。

### 6. 実装後レビュー

- 内容: `isdd-build` の実装後レビューで変更を正本へ反映する（この変更では正本の内容は既に一致しているため、確認と `docs/active_change` の削除）。

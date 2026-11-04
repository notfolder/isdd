# タスク: クレジットカード番号の判定関数の追加

変更要件定義書と変更設計書にもとづく。上から順に実行する。対応する設計 ID を各タスクに書く。

## 0. 実装開始前の固定タスク

### 0. isdd-setup 導入確認タスク

- 対象の設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が存在し、`scripts/isdd/completeness.json` の実行形態（library）・認証（なし）・外部連携（なし）が詳細設計書と一致していることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- 対象の設計 ID: なし（登録の確認）
- 内容: `docs/active_change` の 1 行目が `.history/20261104-add-is-credit-card/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない。反映は実装後に `isdd-build` の実装後レビューが行う。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-add-is-credit-card/change_requirements.md .history/20261104-add-is-credit-card/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 実装タスク

### 1. 判定関数の追加

- 対象の設計 ID: `DS-FN-IS-CREDIT-CARD`
- 内容: `string_utils/validation.py` の判定関数の並びで、メールの判定関数の次に `is_credit_card(input_string: Any, card_type: str=None) -> bool` を追加する。シグネチャと docstring は既存の正本の書式に合わせ、要件（`RQ-FT-CHECK-CREDIT-CARD`、`RQ-FT-REJECT-UNKNOWN-CARD-TYPE`）の判定内容に従う。空でない文字列の確認を先に行い、文字列でなければ偽を返す。カード種別が省略されたら既知の 6 種のパターンのいずれかに合えば真、指定されたらそのパターンだけで判定する。未知のカード種別は `KeyError` になる。既存の公開関数の一覧（`__all__`）には既に載っているので変えない。
- 完了条件: `python3 -c "import string_utils"` が例外なく通ること（現状は `__all__` の定義欠落で失敗している）。既存の単体テストが全件通ること（後述のタスク 3 で確認）。

### 2. 単体テストの追加

- 対象の設計 ID: `DS-FN-IS-CREDIT-CARD`
- 内容: `tests/test_is_credit_card.py` を新しく作り、既存のテストと同じ `unittest` の書式で、既知の 6 種の正しい番号と誤った番号、空・空白・文字列以外、未知のカード種別での `KeyError` を確かめる。既存のテストファイルは変更しない。
- 完了条件: `python3 -m pytest tests/test_is_credit_card.py` が全件通ること。

### 3. 単体テスト・結合テスト全件通過タスク

- 対象の設計 ID: `DS-FN-IS-CREDIT-CARD`、既存の全判定・加工・生成の関数
- 内容: 詳細設計書 8-1 の実行コマンド `python3 -m pytest tests` を実行する。
- 完了条件: テスト結果に FAIL と ERROR が 0 件であること。失敗した場合は修正と再実行を繰り返す。

### 4. E2E テストの作成

- 対象の設計 ID: `DS-TS-VERIFY-CREDIT-CARD-CHECK`、既存の `DS-TS-VERIFY-PUBLIC-API-IMPORT`、`DS-TS-VERIFY-VALIDATION-BASICS`、`DS-TS-VERIFY-VALIDATION-TEXT`、`DS-TS-VERIFY-TEXT-TRANSFORM`、`DS-TS-VERIFY-COMPRESS-AND-ROMAN`、`DS-TS-VERIFY-GENERATION`、`DS-TS-VERIFY-PACKAGE-DEPENDENCIES`
- 内容: 詳細設計書 8-2 の各 `DS-TS-*` を、`e2e/` 配下の pytest のテスト関数として作る（ファイルは `e2e/test_*.py`）。テストは公開関数を実際に呼んで、設計書の手順の期待結果を確かめる。対応表の `DS-TS` の行でテスト関数（`e2e/...::関数名`）に結ぶ。`DS-TS-VERIFY-PACKAGE-DEPENDENCIES` は `setup.py` に `install_requires` が無いことと、モジュールの import が標準ライブラリとパッケージ内だけであることを確かめる。
- 完了条件: `e2e/` に 8 つの `DS-TS` に対応するテスト関数があること。

### 5. 対応表（docs/trace_map.md）更新タスク

- 対象の設計 ID: `DS-FN-IS-CREDIT-CARD`、`DS-TS-*`（e2e の各関数）
- 内容: 実装した公開関数 `string_utils/validation.py::is_credit_card` を、`DS-FN-IS-CREDIT-CARD` の行として `docs/trace_map.md` に登録する。`DS-TS-*` の行は、e2e のテスト関数（`e2e/...::関数名`）として登録する。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

### 6. E2E テスト全件通過タスク

- 対象の設計 ID: 8 つの `DS-TS-*`（4 で作ったテスト関数）
- 内容: 詳細設計書 8-4 の実行コマンド `python3 -m pytest e2e --junitxml=e2e/results/e2e.xml` で全件実行する。
- 完了条件: テスト結果に FAIL と ERROR が 0 件であること。失敗した場合は修正と再実行を繰り返し、全件通過まで続ける。

### 7. README.md 記載タスク

- 対象の設計 ID: `DS-OP-PACKAGE-SETUP`
- 内容: README.md に、インストールと使い方（`string_utils` からの import）が書かれていることを確かめる。既存の README に記載があれば、新しい関数を追記する必要は無い（公開関数の一覧に影響が無い）。
- 完了条件: README.md を読むだけで、インストールと公開関数の呼び出しが分かること。

### 8. 起動確認タスク

- 対象の設計 ID: `DS-OP-PACKAGE-SETUP`
- 内容: 実行形態はライブラリ。詳細設計書 第 9 章の手順（`setup.py` で配布物を作り、import する）で、パッケージが読み込めて新しい関数が呼べることを確かめる。
- 完了条件: `python3 -c "from string_utils import is_credit_card; print(is_credit_card('4111111111111111'))"` が例外なく `True` を出すこと。

## 2. 実装完了確認の固定タスク

### 9. 変更点の実装確認タスク

- 対象の設計 ID: `DS-FN-IS-CREDIT-CARD`、`DS-MD-VALIDATION-MODULE`、`DS-TS-VERIFY-CREDIT-CARD-CHECK`
- 内容: 変更要件定義書の [追加] の要件（`RQ-FT-CHECK-CREDIT-CARD`、`RQ-FT-REJECT-UNKNOWN-CARD-TYPE`、`RQ-TS-VERIFY-CREDIT-CARD-CHECK`）が実装されたことを、受け入れ判定の表で確かめる。
- 完了条件: 受け入れ判定の表で、これらの要件が「実装済み」になること。

### 10. 実装完了チェックタスク

- 内容: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK であること。

## 補足: 変更の注意

- 既存の公開関数の挙動は変えない。
- 正本（`docs/requirements.md`・`docs/detail_design.md`）の書き換えは、実装後に `isdd-build` の実装後レビューが行う。

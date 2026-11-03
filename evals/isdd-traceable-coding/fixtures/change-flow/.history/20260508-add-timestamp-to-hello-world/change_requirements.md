# Hello World 出力システム 変更要件定義書（出力に実行時刻を付ける）

既存要件定義書: `docs/requirements.md`

## 1. 目的・前提

- システムの目的: 変更なし。既存要件定義書 `docs/requirements.md` セクション1 を参照
- 用語集（追加）

| 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 | 区分 |
|---|---|---|---|---|
| 実行時刻 | スクリプトを実行した時点のローカル時刻（HH:MM:SS、ミリ秒は含まない） | 出力に付ける時刻 | タイムスタンプ | [追加] |

- システムの形態: 変更なし

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

## 2. 業務

対象業務は変更なし（`RQ-BZ-OUTPUT-VERIFICATION`）。

### 2-1. 業務の問題（追加）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 出力からいつ実行されたかが分からない | `RQ-BZ-OUTPUT-VERIFICATION` | ログや CI の出力だけで実行時刻を特定できる | 出力に実行時刻が無い | 実行時刻を特定できる出力の割合: あるべき姿 100%、現状 0% | 複数回の実行結果を見分けられず、障害調査に時間がかかる |

### 2-2. 業務課題一覧

既存の `RQ-BK-SHARED-VERIFICATION-SCRIPT` は変更なし。

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） | 区分 |
|---|---|---|---|---|---|
| `RQ-BK-OUTPUT-TIMESTAMP` | 出力に実行時刻を付ける | 出力からいつ実行されたかが分からない | すべての出力に実行時刻が付く | `RQ-BZ-OUTPUT-VERIFICATION` | [追加] |

### 2-3. 見込み経営効果

変更なし（追加の効果は算定しない）。

## 3. 機能要件

- 出力データ: [削除] 固定文字列 "Hello, World!" を 1 行 / [追加] "Hello, World! (HH:MM:SS)" を 1 行
- 入力データ、CUI の引数と終了コード: 変更なし

| RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか | 区分 |
|---|---|---|---|---|---|
| `RQ-FT-GET-HELLO-MESSAGE`（deprecated） | 業務機能 | 表示文字列の取得 | `RQ-BK-OUTPUT-TIMESTAMP` | 時刻付きの文字列の生成に置き換えるため削除する | [削除] |
| `RQ-FT-PRINT-HELLO-WORLD`（deprecated） | 業務機能 | Hello, World! の標準出力 | `RQ-BK-OUTPUT-TIMESTAMP` | 時刻付きの出力に置き換えるため削除する | [削除] |
| `RQ-FT-GET-CURRENT-TIME` | 業務機能 | 実行時刻の取得 | `RQ-BK-OUTPUT-TIMESTAMP` | 出力に実行時刻を含められない | [追加] |
| `RQ-FT-BUILD-TIMESTAMPED-MESSAGE` | 業務機能 | 時刻付きメッセージの生成 | `RQ-BK-SHARED-VERIFICATION-SCRIPT`, `RQ-BK-OUTPUT-TIMESTAMP` | 出力する文字列を用意できず検証できない | [追加] |
| `RQ-FT-PRINT-TIMESTAMPED-OUTPUT` | 業務機能 | 時刻付きメッセージの標準出力 | `RQ-BK-SHARED-VERIFICATION-SCRIPT`, `RQ-BK-OUTPUT-TIMESTAMP` | 実行環境の動作を確認する共通手段が無くなる | [追加] |

### 3-1. 帳票・出力ファイル

| RQ-ID | 帳票・出力名 | 形式 | 出力項目 | 出力のきっかけ | 対応業務課題ID（RQ-BK-*） | 区分 |
|---|---|---|---|---|---|---|
| `RQ-UI-HELLO-STDOUT-OUTPUT`（deprecated） | 検証結果の表示 | 標準出力 1 行 | "Hello, World!" | スクリプトの実行 | `RQ-BK-OUTPUT-TIMESTAMP` | [削除] |
| `RQ-UI-TIMESTAMPED-STDOUT-OUTPUT` | 時刻付きの検証結果の表示 | 標準出力 1 行 | "Hello, World! (HH:MM:SS)" | スクリプトの実行 | `RQ-BK-OUTPUT-TIMESTAMP` | [追加] |

### 3-2. 業務ルール

| RQ-ID | ルール名 | 内容（条件と結果） | 違反時・エラー時の業務上の扱い | 対応業務課題ID（RQ-BK-*） | 区分 |
|---|---|---|---|---|---|
| `RQ-FT-TIME-FORMAT-RULE` | 時刻の書式 | ローカル時刻を 24 時間制の HH:MM:SS で表す。ミリ秒は付けない | 時刻を取得できない場合は例外を伝播させ、0 以外で終わる | `RQ-BK-OUTPUT-TIMESTAMP` | [追加] |

### 3-3. 外部連携

変更なし（外部連携は無い）。

## 4. データ

変更なし。既存要件定義書 `docs/requirements.md` セクション4 を参照（DB は不要。状態を持つエンティティは無い）。

## 5. 非機能要件

変更なし。

## 6. 運用要件

変更なし。

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 対応業務課題ID（RQ-BK-*） | 区分 |
|---|---|---|---|---|---|---|
| `RQ-TS-VERIFY-HELLO-WORLD-OUTPUT`（deprecated） | "Hello, World!" の表示の確認 | スクリプトが配置されている | 引数なしで実行する | "Hello, World!" が 1 行 | `RQ-BK-OUTPUT-TIMESTAMP` | [削除] |
| `RQ-TS-VERIFY-TIMESTAMPED-OUTPUT` | 時刻付きの表示の確認 | スクリプトが配置されている | 引数なしで実行する | "Hello, World! (HH:MM:SS)" が 1 行表示され、終了コード 0 で終わる | `RQ-BK-SHARED-VERIFICATION-SCRIPT`, `RQ-BK-OUTPUT-TIMESTAMP` | [追加] |

## 8. 業務課題と要件の対応表（変更後）

| RQ-BK-ID | 対応要件ID |
|---|---|
| `RQ-BK-SHARED-VERIFICATION-SCRIPT` | `RQ-FT-BUILD-TIMESTAMPED-MESSAGE`, `RQ-FT-PRINT-TIMESTAMPED-OUTPUT`, `RQ-DT-DB-NOT-REQUIRED`, `RQ-TS-VERIFY-TIMESTAMPED-OUTPUT` |
| `RQ-BK-OUTPUT-TIMESTAMP` | `RQ-FT-GET-CURRENT-TIME`, `RQ-FT-BUILD-TIMESTAMPED-MESSAGE`, `RQ-FT-PRINT-TIMESTAMPED-OUTPUT`, `RQ-FT-TIME-FORMAT-RULE`, `RQ-UI-TIMESTAMPED-STDOUT-OUTPUT`, `RQ-TS-VERIFY-TIMESTAMPED-OUTPUT` |

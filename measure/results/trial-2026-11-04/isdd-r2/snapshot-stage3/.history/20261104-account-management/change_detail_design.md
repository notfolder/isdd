# 変更設計書: アカウントの管理（段 3）

対象の正本: `docs/detail_design.md`。変更要件定義書: `.history/20261104-account-management/change_requirements.md`。この変更は正本を書き換えない。反映は実装後に `isdd-build` の実装後レビューが行う。

## 0. 変更の概要

変更要件の [追加] は、受け入れテスト 1 件（`RQ-TS-ACCESS-ENDS-ON-RESET-AND-DELETE`）だけ。その振る舞いは既存の設計で満たしている。
- パスワードの再設定（DS-FN-RESET-PASSWORD）は、ハッシュを新しい値で置き換える。古いパスワードは照合で一致しなくなる。
- アカウントの削除（DS-FN-DELETE-ACCOUNT）は、アカウントの行とそのセッションを消す。削除したアカウントは照合（DS-FN-AUTHENTICATE-ACCOUNT）で一致せず、貸出の登録の社員の一覧（DS-FN-LIST-ACCOUNTS）にも出ない。

このため、設計要素（DS-MD・DS-CL・DS-FN・DS-IF・DS-SC）は追加も削除もしない。設計要素に増えるのは受け入れテストの DS-TS-ACCESS-ENDS-ON-RESET-AND-DELETE（E2E の関数 1 件）だけ。
画面の入口の文言（担当者の「備品を登録」）は実装の差分で、ID を増やさず、実装後レビューで DS-IF-LENDING-STATUS-SCREEN の説明に反映する。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照

## 4. アーキテクチャ設計

変更なし。既存設計 `docs/detail_design.md` セクション 4 を参照

## 5. クラス設計

変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照

## 6. エラーハンドリングとセキュリティ設計

変更なし。既存設計 `docs/detail_design.md` セクション 6 を参照

## 7. コード設計

変更なし。既存設計 `docs/detail_design.md` セクション 7 を参照（新しいソースファイルは無い）

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存設計 `docs/detail_design.md` セクション 8-1 を参照

### 8-2. E2E テストのシナリオ

| 区分 | DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| [追加] | DS-TS-ACCESS-ENDS-ON-RESET-AND-DELETE | RQ-TS-ACCESS-ENDS-ON-RESET-AND-DELETE の確認 | 担当者 1 人、社員 A と B（借りていない）、空きの備品 1 件。担当者でログイン | 社員 A のパスワードを再設定し、古いパスワードでログインを試す。社員 B を削除し、社員 B でログインを試す。貸出の登録の画面を開く | 再設定は「パスワードを再設定しました」。古いパスワードと削除した社員 B のログインは「社員番号またはパスワードが違います」（`.error`）。借りる社員の選択肢に A は出て、B は出ない |

非機能の確認と、既存の E2E テストの設計は変更なし。実行コマンドは 8-4 のまま。

### 8-3. E2E の実行手段

変更なし。既存設計 `docs/detail_design.md` セクション 8-3 を参照

### 8-4. E2E の実行コマンドと運用

変更なし。既存設計 `docs/detail_design.md` セクション 8-4 を参照

## 9. 運用設計

変更なし。既存設計 `docs/detail_design.md` セクション 9 を参照

## 10. ログ・監視・アラート・障害対応設計

変更なし。既存設計 `docs/detail_design.md` セクション 10 を参照

## 11. 要件と設計の対応表

| 区分 | DS-ID | 対応要件ID |
|---|---|---|
| [追加] | DS-TS-ACCESS-ENDS-ON-RESET-AND-DELETE | RQ-TS-ACCESS-ENDS-ON-RESET-AND-DELETE |
| 変更なし（既存） | DS-FN-RESET-PASSWORD | RQ-FT-RESET-PASSWORD |
| 変更なし（既存） | DS-FN-DELETE-ACCOUNT | RQ-FT-DELETE-ACCOUNT |
| 変更なし（既存） | DS-FN-AUTHENTICATE-ACCOUNT | RQ-FT-RULE-LOGIN-FAILURE-GENERIC |
| 変更なし（既存） | DS-FN-LIST-ACCOUNTS | RQ-FT-LIST-ACCOUNTS |
| 変更なし（既存） | DS-IF-LENDING-FORM-SCREEN | RQ-UI-LENDING-FORM-SCREEN |
| 変更なし（既存） | DS-IF-LENDING-STATUS-SCREEN | RQ-UI-LENDING-STATUS-SCREEN, RQ-NF-RESPONSE-TIME-3S |
| 変更なし（既存） | DS-IF-ACCOUNT-LIST-SCREEN | RQ-UI-ACCOUNT-LIST-SCREEN |
| 変更なし（既存） | DS-FN-CHANGE-MANAGER-ROLE | RQ-FT-CHANGE-MANAGER-ROLE, RQ-FT-RULE-AT-LEAST-ONE-MANAGER |
| 変更なし（既存） | DS-TS-MANAGE-MANAGER-ROLE | RQ-TS-MANAGE-MANAGER-ROLE |

### 11-1. 除外要件

除外要件は無い。

### 11-2. 補足（対応の根拠）

変更なし（既存）の行は、既存の設計要素が変更要件の要件を満たすことを表す。DS-IF-LENDING-STATUS-SCREEN の入口の文言（担当者の「備品を登録」「アカウントの一覧」）は、正本の設計の説明文に書き足す（ID は変えない）。

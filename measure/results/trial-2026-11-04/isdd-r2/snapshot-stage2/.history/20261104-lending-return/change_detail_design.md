# 変更設計書: 貸出と返却（段 2）

対象の正本: `docs/detail_design.md`。変更要件定義書: `.history/20261104-lending-return/change_requirements.md`。この変更は正本を書き換えない。反映は実装後に `isdd-build` の実装後レビューが行う。

## 0. 変更の概要

変更要件の 2 つの業務ルール（修正での貸出の引き継ぎ、同時の貸出と返却の扱い）は、既存の設計で実現している。
- 修正（DS-FN-UPDATE-EQUIPMENT）は備品の行だけを更新し、貸出の行（`lendings`）に触れない。貸出の行は備品の id で結ぶ。
- 貸出（DS-FN-LEND-EQUIPMENT）と返却（DS-FN-RETURN-EQUIPMENT）は `BEGIN IMMEDIATE` で直列化し、貸出の行の主キーで二重の貸出を防ぐ。後の処理は既存の結果の知らせ（「既に貸出中」「既に返却されています」）になる。

このため、設計要素（DS-MD・DS-FN・DS-IF・DS-SC）は追加も削除もしない。変えるのは、受け入れテストの設計（8-2）と対応表（第 11 章）だけ。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照（3-2 の排他制御の表は、既存の貸出と返却の行がそのまま変更要件を満たす）

## 4. アーキテクチャ設計

変更なし。既存設計 `docs/detail_design.md` セクション 4 を参照

## 5. クラス設計

変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照

## 6. エラーハンドリングとセキュリティ設計

変更なし。既存設計 `docs/detail_design.md` セクション 6 を参照

## 7. コード設計

変更なし。既存設計 `docs/detail_design.md` セクション 7 を参照（新しいソースファイルは無い。テストは `e2e/test_equipment.py` に追加する）

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存設計 `docs/detail_design.md` セクション 8-1 を参照

### 8-2. E2E テストのシナリオ

| 区分 | DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| [追加] | DS-TS-KEEP-LENDING-ON-UPDATE | RQ-TS-KEEP-LENDING-ON-UPDATE の確認 | 担当者でログイン。備品 1 件が社員に貸出中 | 備品の修正画面で備品名だけを変えて保存し、貸出状況を開く | 保存は成功。貸出状況で同じ備品が貸出中のまま、借りている社員の名前と貸出日が修正前と同じ |
| [追加] | DS-TS-CONCURRENT-LEND-RETURN | RQ-TS-CONCURRENT-LEND-RETURN の確認 | 担当者 A と B。空きの備品 1 件と社員 1 人（貸出の確認）。貸出中の備品 1 件（返却の確認） | A と B が同じ空きの備品の貸出を同時に送る。続けて A と B が同じ貸出中の備品の返却を同時に送る | 貸出は一方が「貸出を登録しました」、他方が「この備品は既に貸出中です」。返却は一方が「返却を登録しました」、他方が「この備品は既に返却されています」。貸出状況は「空き」 |

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
| [追加] | DS-TS-KEEP-LENDING-ON-UPDATE | RQ-TS-KEEP-LENDING-ON-UPDATE |
| [追加] | DS-TS-CONCURRENT-LEND-RETURN | RQ-TS-CONCURRENT-LEND-RETURN |
| 変更なし（既存） | DS-FN-UPDATE-EQUIPMENT | RQ-FT-RULE-KEEP-LENDING-ON-UPDATE, RQ-FT-UPDATE-EQUIPMENT |
| 変更なし（既存） | DS-FN-LEND-EQUIPMENT | RQ-FT-RULE-CONCURRENT-LEND-RETURN, RQ-FT-LEND-EQUIPMENT |
| 変更なし（既存） | DS-FN-RETURN-EQUIPMENT | RQ-FT-RULE-CONCURRENT-LEND-RETURN, RQ-FT-RETURN-EQUIPMENT |
| 変更なし（既存） | DS-IF-EQUIPMENT-FORM-SCREEN | RQ-UI-EQUIPMENT-FORM-SCREEN |

### 11-1. 除外要件

除外要件は無い。

### 11-2. 補足（対応の根拠）

変更なし（既存）の行は、既存の設計要素が変更要件の要件を満たすことを表す。根拠は 0 に書いた。

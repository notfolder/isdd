---
name: isdd-id-definitions
description: >
  isdd仕様駆動開発で使用する全IDの定義を管理するスキル。
  要件ID（RQ-*）・設計ID（DS-*）・スキル固有IDの命名規則・カテゴリ・採番ルールを一元管理する唯一の情報源（Single Source of Truth）。
  「IDの定義を確認したい」「新しいIDを採番したい」「RQ-*やDS-*のルールを知りたい」「isddのID体系を参照したい」などの依頼では必ずこのスキルを使うこと。
  他の全isddスキルはIDを採番・参照する前に必ずこのスキルを参照すること。
---

# isdd-id-definitions — isdd ID定義スキル

isdd仕様駆動開発で使用する全IDの定義を管理する、唯一の情報源（Single Source of Truth）。
要件ID（RQ-*）・設計ID（DS-*）・スキル固有IDの命名規則を規定する。

---

## 要件ID（RQ-*）体系

### フォーマット

```
RQ-[カテゴリ]-[内容略称]
```

- 内容略称: 英語ALL CAPSケバブケース（例: `CREATE-ORDER`）
- 連番なし、意味を表すスラッグのみ

### カテゴリ一覧（7種）

| カテゴリ | プレフィックス | 対象 |
|---|---|---|
| 機能 | `RQ-FT` | 業務機能・ユースケース |
| 画面 | `RQ-UI` | 画面・UI要件 |
| 外部連携 | `RQ-EX` | 外部システム連携 |
| テストシナリオ | `RQ-TS` | テスト要件 |
| 非機能 | `RQ-NF` | 性能・可用性・セキュリティ等 |
| データ | `RQ-DT` | データ定義・保持ポリシー |
| 運用 | `RQ-OP` | 運用・バックアップ・監視 |

### 内容略称の命名規則（カテゴリ別）

| カテゴリ | 命名パターン | 例 |
|---|---|---|
| `RQ-FT`、`RQ-EX`、`RQ-TS` | 動詞先頭 | `CREATE-ORDER`、`SYNC-CUSTOMER-MASTER`、`VERIFY-ORDER-CANCEL` |
| `RQ-UI` | 画面名先頭 | `ORDER-CREATE-SCREEN`、`CUSTOMER-LIST-SCREEN` |
| `RQ-NF`、`RQ-DT`、`RQ-OP` | 名詞先頭 | `RESPONSE-TIME-2S`、`CUSTOMER-DATA-RETENTION`、`BACKUP-DAILY-POLICY` |

---

## 設計ID（DS-*）体系

### フォーマット

```
DS-[DSカテゴリ]-[DS内容略称]-[RQカテゴリ]-[RQ内容略称]
```

末尾の `[RQカテゴリ]-[RQ内容略称]` は、この設計要素が対応する要件IDの略称部分を表す。

### DSカテゴリ一覧（7種）

| カテゴリ | プレフィックス | 対象 |
|---|---|---|
| モジュール | `DS-MD` | モジュール・コンポーネント単位 |
| APIインターフェース | `DS-IF` | API・インターフェース定義 |
| クラス | `DS-CL` | クラス設計 |
| 関数 | `DS-FN` | 関数・メソッド設計 |
| データモデル | `DS-SC` | スキーマ・データモデル |
| バッチ | `DS-BT` | バッチ・ジョブ設計 |
| イベント | `DS-EV` | イベント・メッセージ設計 |

### ID例

| 要件ID | 設計ID | 説明 |
|---|---|---|
| `RQ-FT-CREATE-ORDER` | `DS-FN-CREATE-ORDER-FT-CREATE-ORDER` | 注文作成機能の関数 |
| `RQ-FT-CREATE-ORDER` | `DS-CL-ORDER-SERVICE-FT-CREATE-ORDER` | 注文作成機能のサービスクラス |
| `RQ-EX-SYNC-CUSTOMER-MASTER` | `DS-IF-SYNC-CUSTOMER-MASTER-EX-SYNC-CUSTOMER-MASTER` | 顧客マスタ同期APIインターフェース |

---

## スキル固有ID一覧

各isddスキルが定義・使用するスキル固有のIDを一覧で管理する。

### isdd-external-research スキル固有ID（RQ-EX カテゴリ）

外部システム連携のモック戦略を識別するIDで、isdd-external-researchスキルが採番・使用する。

| ID | モック戦略 | 適用条件 |
|---|---|---|
| `RQ-EX-USE-LOCAL-HTTP-MOCK` | ローカルHTTPサーバー方式（方式A） | 状態保持、CRUD、複雑認証の再現が必要な場合 |
| `RQ-EX-USE-FIXED-RESPONSE-MOCK` | 固定レスポンスファイル方式（方式B） | 静的レスポンス中心、プロトタイプ重視の場合 |
| `RQ-EX-USE-MOCK-SERVER-TOOL` | 既存モックサーバーツール方式（方式C） | 複数連携先対応、障害注入や遅延制御が必要な場合 |

---

## ID採番ガイドライン

### 新しいRQ-*を採番するとき

1. カテゴリを7種から選ぶ（「どのカテゴリか判断できない」場合はユーザーに確認する）
2. 内容略称をカテゴリ別命名規則に従って決める
3. 既存IDと衝突しないか `docs/requirements.md` を確認する

### 新しいDS-*を採番するとき

1. DSカテゴリを7種から選ぶ
2. DS内容略称を決める（対応するRQ-*の内容略称を流用するケースが多い）
3. 対応するRQ-*を末尾に付与する

### 変更管理ルール

| 変更の種類 | 対応 |
|---|---|
| 要件の**意味が変わる**場合 | 旧IDを `.history/` 配下の変更記録内で `deprecated` としてマーク → 新IDで新要件を登録 |
| 要件の**表現・表記のみが変わる**場合（意味は同一） | 同IDのまま更新 |

- `deprecated` となったIDは `docs/requirements.md` と `docs/detail_design.md` から**削除する**
- これらのドキュメントは常に現在有効なIDのみを記載する

---

## 他スキルからの参照方法

isdd配下の各スキルは、IDを採番・コメントへ記載する際、必ずこのスキル（isdd-id-definitions）のID定義を参照する。
各スキルのSKILL.mdにはIDの完全定義を再掲せず、「isdd-id-definitionsを参照」と記載する。

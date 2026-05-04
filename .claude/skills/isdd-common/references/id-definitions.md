# isdd ID定義（要件ID・設計ID）

isdd仕様駆動開発で使用する ID 体系の完全定義。全スキルの唯一の情報源（Single Source of Truth）。

---

## 要件ID（RQ-*）体系

### フォーマット

```
RQ-[カテゴリ]-[内容略称]
```

- 内容略称：英語 ALL CAPS ケバブケース（例: `CREATE-ORDER`）
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

末尾の `[RQカテゴリ]-[RQ内容略称]` は、この設計要素が対応する要件 ID の略称部分を表す。

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
| `RQ-EX-SYNC-CUSTOMER-MASTER` | `DS-IF-SYNC-CUSTOMER-MASTER-EX-SYNC-CUSTOMER-MASTER` | 顧客マスタ同期 API インターフェース |

---

## スキル固有ID一覧

各 isdd スキルが定義・使用するスキル固有の ID を一覧で管理する。

### isdd-external-research スキル固有ID（RQ-EX カテゴリ）

外部システム連携のモック戦略を識別する ID で、isdd-external-research スキルが採番・使用する。

| ID | モック戦略 | 適用条件 |
|---|---|---|
| `RQ-EX-USE-LOCAL-HTTP-MOCK` | ローカル HTTP サーバー方式（方式A） | 状態保持、CRUD、複雑認証の再現が必要な場合 |
| `RQ-EX-USE-FIXED-RESPONSE-MOCK` | 固定レスポンスファイル方式（方式B） | 静的レスポンス中心、プロトタイプ重視の場合 |
| `RQ-EX-USE-MOCK-SERVER-TOOL` | 既存モックサーバーツール方式（方式C） | 複数連携先対応、障害注入や遅延制御が必要な場合 |

---

## ID採番ガイドライン

### 新しい RQ-* を採番するとき

1. カテゴリを 7 種から選ぶ（「どのカテゴリか判断できない」場合はユーザーに確認する）
2. 内容略称をカテゴリ別命名規則に従って決める
3. 既存 ID と衝突しないか `docs/requirements.md` を確認する

### 新しい DS-* を採番するとき

1. DS カテゴリを 7 種から選ぶ
2. DS 内容略称を決める（対応する RQ-* の内容略称を流用するケースが多い）
3. 対応する RQ-* を末尾に付与する

### 変更管理ルール

| 変更の種類 | 対応 |
|---|---|
| 要件の**意味が変わる**場合 | 旧 ID を `.history/` 配下の変更記録内で `deprecated` としてマーク → 新 ID で新要件を登録 |
| 要件の**表現・表記のみが変わる**場合（意味は同一） | 同 ID のまま更新 |

- `deprecated` となった ID は `docs/requirements.md` と `docs/detail_design.md` から**削除する**
- これらのドキュメントは常に現在有効な ID のみを記載する

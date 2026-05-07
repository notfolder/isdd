# 備品管理・貸出管理アプリ 詳細設計書

---

## 1. 言語・フレームワーク

| DS-ID | 対象 | 採用技術 | バージョン | 選定理由 |
|---|---|---|---|---|
| DS-MD-FRONTEND-FT-VIEW-EQUIPMENT-LIST | フロントエンド | Vue 3 + Vuetify 3 | Vue 3.x / Vuetify 3.x | ロール別ルーティングと複数画面の複雑な遷移が必要なため、Streamlit（単一ページ向け）ではなくVue+Vuetifyを選定 |
| DS-MD-BACKEND-FT-MANAGE-EQUIPMENT | バックエンド | Python + FastAPI | Python 3.12 / FastAPI 0.115 | isddのデフォルト言語はPythonであり、非同期対応・Pydantic統合・応答3秒以内の非機能要件を満たせる |
| DS-MD-DATABASE-DT-EQUIPMENT-ENTITY | DB | SQLite | SQLite 3 | 備品最大100件・利用者最大30人の小規模データのため外部DBサーバー不要 |
| DS-MD-E2E-TEST-TS-VERIFY-ADMIN-LOGIN | E2Eテスト | Playwright | 1.59.0 | 全画面遷移シナリオを自動テストするため |
| DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER | 外部DB連携 | SQLAlchemy 2.0 + psycopg2-binary | 2.0.x / 2.9.x | Neon PostgreSQL への接続。NullPool + channel_binding=require に対応する唯一の構成。既存の SQLAlchemy 統一方針に整合 |
| DS-MD-DOTENV-EX-FETCH-DEPARTMENT-MASTER | 環境変数 | python-dotenv | 1.x | 外部DB接続 URL を .env から読み込むため |

### フロントエンド構成方針

- Vue 3 SPA をマルチステージビルド後、Nginx で配信する
- バックエンドは Nginx でリバースプロキシを設定する
- API エンドポイントは `/api/` に統一する

---

## 2. システム構成

### コンポーネント一覧

| DS-ID | コンポーネント | 役割 | 根拠要件 |
|---|---|---|---|
| DS-MD-FRONTEND-FT-VIEW-EQUIPMENT-LIST | フロントエンド（Vue3 + Nginx） | 全画面の提供、/api/ をバックエンドへプロキシ | RQ-UI-WEB-GUI |
| DS-MD-BACKEND-FT-MANAGE-EQUIPMENT | バックエンド（FastAPI + uvicorn） | 全APIエンドポイント、認証認可、ビジネスロジック | RQ-FT-LOGIN〜RQ-FT-RETURN-EQUIPMENT |
| DS-MD-DATABASE-DT-EQUIPMENT-ENTITY | DB（SQLite） | 備品・利用者・現在の貸出状態・予約の永続化 | RQ-DT-APP-DATABASE-REQUIRED |
| DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER | 外部DB（Neon PostgreSQL） | 部署マスタ（demo_departments・demo_users）を保持する外部 PostgreSQL | RQ-EX-FETCH-DEPARTMENT-MASTER |

### システム全体構成図

```mermaid
graph LR
    Browser[ブラウザ] --> Nginx["Nginx\nVue3 SPA配信\n/api/ プロキシ"]
    Nginx --> FastAPI["FastAPI\nバックエンド"]
    FastAPI --> SQLite[("SQLite\n内部DB")]
    FastAPI --> NeonDB[("Neon PostgreSQL\n外部DB（部署マスタ）")]
```

### ネットワーク構成図

```mermaid
graph TD
    user[ブラウザ] --> frontend
    subgraph "Docker Compose ネットワーク"
        frontend["frontend\nNginx:80"]
        backend["backend\nuvicorn:8000（非公開）"]
        frontend -- "/api/ proxy" --> backend
        backend --> db[("data/app.db\nSQLiteボリューム")]
    end
    backend -- "EXTERNAL_DB_URL\nSSL必須" --> neon[("Neon PostgreSQL\n外部DB")]
```

---

## 3. データベース設計

SQLite を採用する。備品最大100件・利用者最大30人の小規模データのため、外部DBサーバーを立てるオーバーヘッドは不要であり、SQLiteで要件を満たせる。

### テーブル設計

#### equipmentテーブル（DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY）

| カラム名 | 型 | 制約 | 説明 |
|---|---|---|---|
| equipment_id | TEXT | PRIMARY KEY | 管理者が入力する備品ID（例：PC-001） |
| name | TEXT | NOT NULL | 備品名 |
| status | TEXT | NOT NULL DEFAULT 'available' | 'available'（在庫）・'reserved'（予約済み）・'loaned'（貸出中）の3値 |

**ステータス遷移規則 (DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY):**

| 遷移 | 条件 | 操作 |
|---|---|---|
| available → reserved | 予約作成時に有効な予約が初めて登録される | ReservationService.create 内で自動更新 |
| reserved → available | 予約キャンセル後に有効な予約が0件になる（かつ貸出中でない） | ReservationService.cancel 内で自動更新 |
| available/reserved → loaned | 貸出操作 | EquipmentService.loan 内で更新 |
| loaned → reserved | 返却操作後に end_date < 返却日 の予約を削除し、残予約が1件以上ある | EquipmentService.return_equipment 内で更新 |
| loaned → available | 返却操作後に end_date < 返却日 の予約を削除し、残予約が0件 | EquipmentService.return_equipment 内で更新 |

#### userテーブル（DS-SC-USER-DT-BORROWER-ENTITY）

| カラム名 | 型 | 制約 | 説明 |
|---|---|---|---|
| login_id | TEXT | PRIMARY KEY | ログインID（一意） |
| display_name | TEXT | NOT NULL | 利用者名（貸出先として表示） |
| password_hash | TEXT | NOT NULL | bcryptハッシュ化済みパスワード |
| role | TEXT | NOT NULL | 'admin'（管理者）または 'general'（一般利用者） |

#### loan_stateテーブル（DS-SC-LOAN-STATE-DT-LOAN-STATE-ENTITY）

| カラム名 | 型 | 制約 | 説明 |
|---|---|---|---|
| equipment_id | TEXT | PRIMARY KEY, FK→equipment.equipment_id | 貸出中の備品ID（1備品に1レコードのみ） |
| user_login_id | TEXT | NOT NULL, FK→user.login_id | 貸出先利用者のログインID |
| loan_date | TEXT | NOT NULL | 貸出日（ISO 8601形式、例：2026-05-05） |

返却時は loan_state レコードを削除し、equipment.status を 'available' または 'reserved' に更新する（1トランザクション）。

#### reservationテーブル（DS-SC-RESERVATION-DT-RESERVATION-ENTITY）

| カラム名 | 型 | 制約 | 説明 |
|---|---|---|---|
| reservation_id | TEXT | PRIMARY KEY | UUID 形式の予約ID（自動生成） |
| equipment_id | TEXT | NOT NULL, FK→equipment.equipment_id ON DELETE CASCADE | 予約対象の備品ID |
| user_login_id | TEXT | NOT NULL, FK→user.login_id | 予約者のログインID |
| start_date | TEXT | NOT NULL | 予約開始日（ISO 8601形式、例: 2026-06-01） |
| end_date | TEXT | NOT NULL | 予約終了日（ISO 8601形式、例: 2026-06-05）。start_date 以降であること |

ON DELETE CASCADE を equipment.equipment_id FK に設定する。備品削除時に対象備品の予約レコードを全て自動削除する。

### リレーション図

```mermaid
erDiagram
    equipment {
        TEXT equipment_id PK
        TEXT name
        TEXT status
    }
    user {
        TEXT login_id PK
        TEXT display_name
        TEXT password_hash
        TEXT role
    }
    loan_state {
        TEXT equipment_id PK
        TEXT user_login_id
        TEXT loan_date
    }
    reservation {
        TEXT reservation_id PK
        TEXT equipment_id FK
        TEXT user_login_id FK
        TEXT start_date
        TEXT end_date
    }
    equipment ||--o| loan_state : "has"
    user ||--o{ loan_state : "borrowed_by"
    equipment ||--o{ reservation : "has"
    user ||--o{ reservation : "made_by"
```

### データ整合性・業務制約

| DS-ID | 制約 | 実装箇所 |
|---|---|---|
| DS-FN-VALIDATE-EQUIPMENT-DELETE-DT-EQUIPMENT-ENTITY | status が 'loaned' の備品は削除不可。削除操作は status 確認後のみ実行 | EquipmentService.delete |
| DS-FN-VALIDATE-USER-DELETE-DT-BORROWER-ENTITY | 現在貸出中の貸出先・自分自身・最後の管理者利用者は削除不可 | UserService.delete |
| DS-FN-VALIDATE-LAST-ADMIN-DT-BORROWER-ENTITY | 管理者が1人の場合、その利用者の role を general に変更不可 | UserService.update |
| DS-FN-VALIDATE-LOAN-AVAILABLE-DT-LOAN-STATE-ENTITY | status が 'loaned' の備品への再貸出は不可。status が 'available' または 'reserved' の場合のみ貸出可 | EquipmentService.loan |
| DS-FN-VALIDATE-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION | 同一備品に対し期間が1日以上重なる予約の登録を禁止する。SELECT COUNT 後に INSERT を同一トランザクション内で実行し、SQLite のライトロックで競合を防ぐ | ReservationService.create |
| DS-FN-VALIDATE-RESERVATION-CANCEL-FT-CANCEL-RESERVATION | 予約のキャンセルは予約者本人または管理者のみ可能 | ReservationService.cancel |

---

## 4. アーキテクチャ設計

### 4.1 外部設計

#### 画面一覧

| DS-ID | 画面名 | 対応RQ-UI-ID | 利用者 |
|---|---|---|---|
| DS-MD-LOGIN-VIEW-UI-LOGIN-SCREEN | ログイン画面 | RQ-UI-LOGIN-SCREEN | 全員 |
| DS-MD-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN | 管理者向け備品一覧画面 | RQ-UI-ADMIN-EQUIPMENT-LIST-SCREEN | 管理者 |
| DS-MD-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN | 備品登録・編集画面 | RQ-UI-EQUIPMENT-FORM-SCREEN | 管理者 |
| DS-MD-EQUIPMENT-DELETE-VIEW-UI-EQUIPMENT-DELETE-CONFIRM-SCREEN | 備品削除確認画面 | RQ-UI-EQUIPMENT-DELETE-CONFIRM-SCREEN | 管理者 |
| DS-MD-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN | 貸出登録画面 | RQ-UI-LOAN-FORM-SCREEN | 管理者 |
| DS-MD-RETURN-CONFIRM-VIEW-UI-RETURN-CONFIRM-SCREEN | 返却確認画面 | RQ-UI-RETURN-CONFIRM-SCREEN | 管理者 |
| DS-MD-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN | 利用者一覧画面 | RQ-UI-BORROWER-LIST-SCREEN | 管理者 |
| DS-MD-USER-FORM-VIEW-UI-BORROWER-FORM-SCREEN | 利用者登録・編集画面 | RQ-UI-BORROWER-FORM-SCREEN | 管理者 |
| DS-MD-USER-DELETE-VIEW-UI-BORROWER-DELETE-CONFIRM-SCREEN | 利用者削除確認画面 | RQ-UI-BORROWER-DELETE-CONFIRM-SCREEN | 管理者 |
| DS-MD-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN | 一般利用者向け備品一覧画面 | RQ-UI-GENERAL-EQUIPMENT-LIST-SCREEN | 一般利用者 |
| DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN | 備品別予約詳細・カレンダー画面 | RQ-UI-RESERVATION-CALENDAR-SCREEN | 全利用者 |
| DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN | 予約登録画面 | RQ-UI-RESERVATION-FORM-SCREEN | 全利用者 |

#### 画面AAモックアップ

**DS-MD-LOGIN-VIEW-UI-LOGIN-SCREEN: ログイン画面**
```
┌──────────────────────────────────┐
│      備品貸出管理システム        │
├──────────────────────────────────┤
│  ログインID  [________________]  │
│  パスワード  [________________]  │
│                                  │
│         [  ログイン  ]           │
│                                  │
│  ※ 認証失敗時: エラーメッセージ │
└──────────────────────────────────┘
```

**DS-MD-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN: 管理者向け備品一覧画面**
```
┌─────────────────────────────────────────────────────────────────────┐
│ 備品一覧 (管理者)                      [利用者管理]  [ログアウト]  │
├─────────────────────────────────────────────────────────────────────┤
│ [+ 備品登録]                                                        │
├────────┬──────────┬──────────┬─────────────────────┬──────────────┤
│ 備品ID │ 備品名   │ 状態     │ 貸出先（部署）      │ 操作         │
├────────┼──────────┼──────────┼─────────────────────┼──────────────┤
│ PC-001 │MacBook A │ 貸出中   │山田太郎（営業部）   │[返却][予約状況]│
├────────┼──────────┼──────────┼─────────────────────┼──────────────┤
│ PC-002 │MacBook B │ 予約済み │                     │[貸出][削除][予約状況]│
├────────┼──────────┼──────────┼─────────────────────┼──────────────┤
│ PC-003 │Surface C │ 在庫     │                     │[貸出][削除][予約状況]│
└────────┴──────────┴──────────┴─────────────────────┴──────────────┘
```
※ 部署名は画面描画後に非同期取得。取得前は「取得中...」を表示。
※ 「貸出」ボタンは status が 'available' または 'reserved' の場合に表示。

**DS-MD-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN: 備品登録・編集画面**
```
┌──────────────────────────────────┐
│ 備品登録 / 備品編集              │
├──────────────────────────────────┤
│ 備品ID  [__________________]     │
│         ※ 新規登録時のみ入力可  │
│ 備品名  [__________________]     │
│                                  │
│       [保存]   [キャンセル]      │
│                                  │
│ ※ バリデーションエラー表示      │
└──────────────────────────────────┘
```

**DS-MD-EQUIPMENT-DELETE-VIEW-UI-EQUIPMENT-DELETE-CONFIRM-SCREEN: 備品削除確認画面**
```
┌──────────────────────────────────┐
│ 備品削除確認                     │
├──────────────────────────────────┤
│ 備品ID  : PC-002                 │
│ 備品名  : MacBook B              │
│ 状態    : 貸出可能               │
│                                  │
│  この備品を削除しますか？        │
│                                  │
│    [削除する]  [キャンセル]      │
└──────────────────────────────────┘
```

**DS-MD-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN: 貸出登録画面**
```
┌──────────────────────────────────────────┐
│ 貸出登録                                 │
├──────────────────────────────────────────┤
│ 備品ID  : PC-002                         │
│ 備品名  : MacBook B                      │
│                                          │
│ 貸出先  [▼ 山田太郎（取得中...）]       │
│ 貸出日  [2026-05-05            ]         │
│                                          │
│        [登録する]  [キャンセル]          │
└──────────────────────────────────────────┘
```
※ ドロップダウン選択肢は「利用者名（部署名）」形式。部署は画面表示後に非同期取得する。取得前は「取得中...」を表示。

**DS-MD-RETURN-CONFIRM-VIEW-UI-RETURN-CONFIRM-SCREEN: 返却確認画面**
```
┌──────────────────────────────────┐
│ 返却確認                         │
├──────────────────────────────────┤
│ 備品ID  : PC-001                 │
│ 備品名  : MacBook A              │
│ 貸出先  : 山田 太郎              │
│ 貸出日  : 2026-05-01             │
│                                  │
│  返却処理を実行しますか？        │
│                                  │
│    [返却する]  [キャンセル]      │
└──────────────────────────────────┘
```

**DS-MD-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN: 利用者一覧画面**
```
┌────────────────────────────────────────────────────────────────┐
│ 利用者一覧              [備品一覧へ戻る]  [ログアウト]         │
├────────────────────────────────────────────────────────────────┤
│ [+ 利用者登録]                                                 │
├────────────┬──────────┬──────────────┬────────────┬──────────┤
│ 利用者名   │ログインID│ 部署         │ 権限       │ 操作     │
├────────────┼──────────┼──────────────┼────────────┼──────────┤
│ 山田 太郎  │ yamada   │ 取得中...    │ 管理者     │[編集][削除]│
├────────────┼──────────┼──────────────┼────────────┼──────────┤
│ 鈴木 花子  │ suzuki   │ 開発部       │ 一般利用者 │[編集][削除]│
└────────────┴──────────┴──────────────┴────────────┴──────────┘
```
※ 部署列は画面描画後に全利用者分を非同期並行取得する。取得前は「取得中...」。一致なし・接続失敗は「不明」を表示。

**DS-MD-USER-FORM-VIEW-UI-BORROWER-FORM-SCREEN: 利用者登録・編集画面**
```
┌──────────────────────────────────┐
│ 利用者登録 / 利用者編集          │
├──────────────────────────────────┤
│ 利用者名   [__________________]  │
│ ログインID [__________________]  │
│            ※ 新規登録時のみ入力可│
│ パスワード [__________________]  │
│ 権限種別   [▼ 管理者 ]          │
│                                  │
│       [保存]   [キャンセル]      │
└──────────────────────────────────┘
```

**DS-MD-USER-DELETE-VIEW-UI-BORROWER-DELETE-CONFIRM-SCREEN: 利用者削除確認画面**
```
┌──────────────────────────────────┐
│ 利用者削除確認                   │
├──────────────────────────────────┤
│ 利用者名  : 鈴木 花子            │
│ ログインID: suzuki               │
│ 権限種別  : 一般利用者           │
│                                  │
│  この利用者を削除しますか？      │
│                                  │
│    [削除する]  [キャンセル]      │
└──────────────────────────────────┘
```

**DS-MD-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN: 一般利用者向け備品一覧画面**
```
┌──────────────────────────────────────────────────────────┐
│ 備品一覧 (閲覧のみ)                       [ログアウト]   │
├────────┬──────────┬──────────────┬──────────────────────┤
│ 備品ID │ 備品名   │ 状態         │ 操作                 │
├────────┼──────────┼──────────────┼──────────────────────┤
│ PC-001 │ MacBook A│ 貸出中       │ [予約状況]           │
├────────┼──────────┼──────────────┼──────────────────────┤
│ PC-002 │ MacBook B│ 予約済み     │ [予約状況]           │
├────────┼──────────┼──────────────┼──────────────────────┤
│ PC-003 │ Surface C│ 在庫         │ [予約状況]           │
└────────┴──────────┴──────────────┴──────────────────────┘
```

**DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN: 備品別予約詳細・カレンダー画面**
```
┌──────────────────────────────────────────────────────────────────┐
│ 備品予約状況                               [戻る]  [ログアウト]  │
├──────────────────────────────────────────────────────────────────┤
│ 備品ID: PC-002  備品名: MacBook B  状態: 予約済み               │
├──────────────────────────────────────────────────────────────────┤
│ 予約一覧                                                         │
├─────────────────────────┬──────────┬──────────┬────────────────┤
│ 予約者名（部署）         │ 開始日   │ 終了日   │ 操作           │
├─────────────────────────┼──────────┼──────────┼────────────────┤
│ 田中太郎（営業部）       │ 06-01    │ 06-05    │ [キャンセル]   │
├─────────────────────────┼──────────┼──────────┼────────────────┤
│ 鈴木花子（開発部）       │ 06-10    │ 06-15    │                │
├──────────────────────────────────────────────────────────────────┤
│ ≪ 2026年6月 ≫                                      [予約する]   │
│  月  火  水  木  金  土  日                                      │
│                    1   2   3   4   5 ←予約済みハイライト        │
│   6   7   8   9  10  11  12                                      │
│  13  14  15  16  17  18  19                                      │
└──────────────────────────────────────────────────────────────────┘
```
※ 「キャンセル」ボタンは予約者本人の予約行に表示。管理者は全行に表示。
※ 「予約する」ボタンは備品ステータスに関わらず常に表示。

**DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN: 予約登録画面**
```
┌──────────────────────────────────────────────────────┐
│ 予約登録                                             │
├──────────────────────────────────────────────────────┤
│ 備品ID  : PC-002                                     │
│ 備品名  : MacBook B                                  │
│                                                      │
│ 開始日  [2026-06-10              ]（必須）           │
│ 終了日  [2026-06-15              ]（必須）           │
│ ※ 管理者のみ: 予約者 [▼ 利用者を選択]             │
│                                                      │
│         [登録する]  [キャンセル]                     │
│                                                      │
│ ※ 重複エラー時:「指定期間は既に予約されています」   │
└──────────────────────────────────────────────────────┘
```

#### 外部システム連携

| DS-ID | 連携先 | 方向 | 実装ライブラリ |
|---|---|---|---|
| DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER | Neon PostgreSQL（部署マスタ） | 読み取り（SELECT のみ） | external/neon-department-db/src/department_client.py |

**外部DB連携データフロー図 (DS-MD-EXTERNAL-DEPT-DB-EX-FETCH-DEPARTMENT-MASTER):**

```mermaid
sequenceDiagram
    participant FE as フロントエンド
    participant BE as FastAPI
    participant Dept as DepartmentService
    participant Client as RealDepartmentClient / MockDepartmentClient
    participant NeonDB as Neon PostgreSQL

    FE->>BE: GET /api/department/by-login-id?login_id=yamada
    BE->>Dept: get_department_name("yamada")
    Dept->>Client: fetch_department_name_by_login_id("yamada")
    Client->>NeonDB: SELECT d.department_name FROM demo_users u JOIN demo_departments d ON u.department_id=d.department_id WHERE u.user_id='yamada'
    NeonDB-->>Client: "営業部"
    Client-->>Dept: "営業部"
    Dept-->>BE: "営業部"
    BE-->>FE: {"department_name": "営業部"}
```

### 4.2 APIエンドポイント設計

| DS-ID | メソッド | パス | 権限 | 入力スキーマ | 出力スキーマ | エラー |
|---|---|---|---|---|---|---|
| DS-IF-AUTH-LOGIN-FT-LOGIN | POST | /api/auth/login | 不要 | LoginRequest | LoginResponse + HTTP-only Cookie | 401 |
| DS-IF-AUTH-LOGOUT-FT-LOGOUT | POST | /api/auth/logout | 要ログイン | なし | 200 OK / Cookie削除 | 401 |
| DS-IF-EQUIPMENT-LIST-FT-VIEW-EQUIPMENT-LIST | GET | /api/equipment | 要ログイン | なし | EquipmentResponse[] | 401 |
| DS-IF-EQUIPMENT-CREATE-FT-MANAGE-EQUIPMENT | POST | /api/equipment | 管理者のみ | EquipmentCreate | EquipmentResponse | 401/403/409 |
| DS-IF-EQUIPMENT-UPDATE-FT-MANAGE-EQUIPMENT | PUT | /api/equipment/{id} | 管理者のみ | EquipmentUpdate | EquipmentResponse | 401/403/404 |
| DS-IF-EQUIPMENT-DELETE-FT-MANAGE-EQUIPMENT | DELETE | /api/equipment/{id} | 管理者のみ | なし | 204 | 401/403/404/409 |
| DS-IF-EQUIPMENT-LOAN-FT-LOAN-EQUIPMENT | POST | /api/equipment/{id}/loan | 管理者のみ | LoanCreate | EquipmentResponse | 401/403/404/409 |
| DS-IF-EQUIPMENT-RETURN-FT-RETURN-EQUIPMENT | POST | /api/equipment/{id}/return | 管理者のみ | なし | EquipmentResponse | 401/403/404 |
| DS-IF-USER-LIST-FT-MANAGE-BORROWER | GET | /api/users | 管理者のみ | なし | UserResponse[] | 401/403 |
| DS-IF-USER-CREATE-FT-MANAGE-BORROWER | POST | /api/users | 管理者のみ | UserCreate | UserResponse | 401/403/409 |
| DS-IF-USER-UPDATE-FT-MANAGE-BORROWER | PUT | /api/users/{id} | 管理者のみ | UserUpdate | UserResponse | 401/403/404/409 |
| DS-IF-USER-DELETE-FT-MANAGE-BORROWER | DELETE | /api/users/{id} | 管理者のみ | なし | 204 | 401/403/404/409 |
| DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API | GET | /api/department/by-login-id | 要ログイン | login_id（クエリパラメータ） | DeptNameResponse | 401 |
| DS-IF-RESERVATION-LIST-FT-VIEW-RESERVATION-CALENDAR | GET | /api/equipment/{id}/reservations | 要ログイン | なし | ReservationResponse[] | 401/404 |
| DS-IF-RESERVATION-CREATE-FT-MAKE-RESERVATION | POST | /api/equipment/{id}/reservations | 要ログイン | ReservationCreate | ReservationResponse | 401/404/409 |
| DS-IF-RESERVATION-DELETE-FT-CANCEL-RESERVATION | DELETE | /api/reservations/{reservation_id} | 要ログイン | なし | 204 | 401/403/404 |

**DeptNameResponse スキーマ (DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API):**
- `department_name`: str — 部署名。照合失敗・外部DB接続失敗時は "不明"

**ReservationCreate スキーマ (DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION):**
- `start_date`: str（YYYY-MM-DD形式、必須）
- `end_date`: str（YYYY-MM-DD形式、必須、start_date 以降）
- `user_login_id`: str（管理者のみ指定可。一般利用者は自動的に自分のID）

**ReservationResponse スキーマ (DS-EV-RESERVATION-RESPONSE-FT-VIEW-RESERVATION-CALENDAR):**
- `reservation_id`: str
- `equipment_id`: str
- `user_login_id`: str
- `user_display_name`: str（JOIN で取得）
- `start_date`: str
- `end_date`: str

### 4.3 内部設計

#### 処理フロー図

**ログイン処理（DS-FN-PROCESS-LOGIN-FT-LOGIN）**

```mermaid
flowchart TD
    A[POST /api/auth/login 受信] --> B[login_id でユーザー検索]
    B --> C{ユーザー存在？}
    C -->|なし| D[401 返却]
    C -->|あり| E[パスワードハッシュ照合]
    E --> F{照合成功？}
    F -->|失敗| D
    F -->|成功| G[JWT生成（有効期限60分）]
    G --> H[HTTP-only Cookie にセット]
    H --> I[role を含む LoginResponse を返却]
```

**貸出処理（DS-FN-PROCESS-LOAN-FT-LOAN-EQUIPMENT）**

```mermaid
flowchart TD
    A[POST /api/equipment/{id}/loan 受信] --> B[管理者権限チェック]
    B -->|403| X[403 Forbidden]
    B --> C[equipment 取得]
    C -->|なし| Y[404 Not Found]
    C --> D{status == available または reserved？}
    D -->|loaned| Z[409 Conflict]
    D -->|available/reserved| E[トランザクション開始]
    E --> F[loan_state レコード作成]
    F --> G[equipment.status を loaned に更新]
    G --> H[コミット → 200 OK]
```

**返却処理（DS-FN-PROCESS-RETURN-UPDATE-STATUS-FT-RETURN-EQUIPMENT）**

```mermaid
flowchart TD
    A[POST /api/equipment/{id}/return 受信] --> B[管理者権限チェック]
    B -->|403| X[403 Forbidden]
    B --> C[loan_state 取得]
    C -->|なし| Y[404 Not Found]
    C --> D[トランザクション開始]
    D --> E[loan_state 削除]
    E --> F[end_date < 返却日 の予約を削除 ReservationRepository.delete_expired_by_equipment]
    F --> G[同一備品の残予約数確認]
    G -->|1件以上| H[equipment.status を reserved に更新]
    G -->|0件| I[equipment.status を available に更新]
    H --> J[コミット → 200 OK]
    I --> J
```

**初期管理者作成処理（DS-FN-INIT-ADMIN-OP-INITIAL-ADMIN-ENV）**

```mermaid
flowchart TD
    A[アプリ起動時] --> B[環境変数 INITIAL_ADMIN_LOGIN_ID / INITIAL_ADMIN_PASSWORD 読み込み]
    B --> C{user テーブルが空？}
    C -->|空でない| D[スキップ]
    C -->|空| E[パスワードを bcrypt ハッシュ化]
    E --> F[role=admin でユーザーレコード作成]
    F --> G[INFO ログ出力：初期管理者作成完了]
```

**予約登録処理 (DS-FN-PROCESS-CREATE-RESERVATION-FT-MAKE-RESERVATION)**

```mermaid
flowchart TD
    A[POST /api/equipment/{id}/reservations 受信] --> B[ログイン確認]
    B -->|401| X[401 Unauthorized]
    B --> C[equipment 取得]
    C -->|なし| Y[404 Not Found]
    C --> D{一般利用者？}
    D -->|一般利用者| E[user_login_id を自分のIDに固定]
    D -->|管理者| F[user_login_id を入力値から取得]
    E --> G[トランザクション開始]
    F --> G
    G --> H[同一備品の重複期間チェック SELECT COUNT]
    H -->|重複あり| Z[409 Conflict 「指定期間は既に予約されています」]
    H -->|重複なし| I[reservation レコード作成]
    I --> J{equipment.status == available？}
    J -->|available| K[equipment.status を reserved に更新]
    J -->|reserved/loaned| L[status 変更なし]
    K --> M[コミット → 201 Created]
    L --> M
```

**予約キャンセル処理 (DS-FN-PROCESS-CANCEL-RESERVATION-FT-CANCEL-RESERVATION)**

```mermaid
flowchart TD
    A[DELETE /api/reservations/{id} 受信] --> B[ログイン確認]
    B -->|401| X[401]
    B --> C[reservation 取得]
    C -->|なし| Y[404]
    C --> D{本人または管理者？}
    D -->|違う| Z[403 Forbidden]
    D -->|OK| E[トランザクション開始]
    E --> F[reservation 削除]
    F --> G[同一備品の残予約数を確認]
    G -->|0件かつ status != loaned| H[equipment.status を available に更新]
    G -->|1件以上 または loaned| I[status 変更なし]
    H --> J[コミット → 204 No Content]
    I --> J
```

**部署名非同期取得処理 (DS-FN-FETCH-DEPT-ASYNC-FT-FETCH-DEPT-BY-LOGIN-ID)**

```mermaid
flowchart TD
    A[画面描画完了] --> B[ユーザー一覧または貸出先を取得]
    B --> C[各 login_id に対して Fetch API を並行呼び出し]
    C --> D[GET /api/department/by-login-id?login_id=xxx]
    D --> E{レスポンス？}
    E -->|成功| F[department_name で「取得中...」を置き換え]
    E -->|失敗・タイムアウト| G[「不明」で「取得中...」を置き換え]
```

#### トランザクション・排他制御

| DS-ID | 処理 | トランザクション境界 | ロールバック条件 |
|---|---|---|---|
| DS-FN-TRANSACTION-LOAN-DT-LOAN-STATE-ENTITY | 貸出登録 | loan_state 作成 + equipment.status 更新 を1トランザクション | どちらか失敗時にロールバック |
| DS-FN-TRANSACTION-RETURN-DT-LOAN-STATE-ENTITY | 返却処理 | loan_state 削除 + end_date < 返却日の予約削除 + 残予約数確認 + equipment.status 更新 を1トランザクション | どれか失敗時にロールバック |
| DS-FN-TRANSACTION-SINGLE-DT-EQUIPMENT-ENTITY | 備品登録・更新・削除 | 単一テーブル操作 | SQLAlchemy 例外発生時 |
| DS-FN-TRANSACTION-SINGLE-DT-BORROWER-ENTITY | 利用者登録・更新・削除 | 単一テーブル操作 | SQLAlchemy 例外発生時 |
| DS-FN-TRANSACTION-RESERVATION-DT-RESERVATION-ENTITY | 予約登録 | 重複チェック SELECT + reservation INSERT + equipment.status 更新を1トランザクション | どれか失敗時にロールバック。SQLite のライトロックで同時予約の競合を防ぐ |
| DS-FN-TRANSACTION-CANCEL-RESERVATION-DT-RESERVATION-ENTITY | 予約キャンセル | reservation DELETE + equipment.status 更新（条件付き）を1トランザクション | 失敗時にロールバック |

排他制御: SQLite のデフォルト WRITE LOCK を使用する。同時5接続程度の小規模のため楽観ロックは不要。

---

## 5. クラス設計

### クラス一覧と役割

| DS-ID | クラス名 | 役割 | SOLID適合 |
|---|---|---|---|
| DS-CL-AUTH-ROUTER-FT-LOGIN | AuthRouter | ログイン・ログアウト API エンドポイント定義 | S: 認証 API のみ |
| DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT | EquipmentRouter | 備品 CRUD・貸出・返却 API エンドポイント定義 | S: 備品 API のみ |
| DS-CL-USER-ROUTER-FT-MANAGE-BORROWER | UserRouter | 利用者 CRUD API エンドポイント定義 | S: 利用者 API のみ |
| DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API | DepartmentRouter | 部署名取得 API エンドポイント定義（GET /api/department/by-login-id） | S: 部署 API のみ |
| DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION | ReservationRouter | 予約 CRUD API エンドポイント定義 | S: 予約 API のみ |
| DS-CL-AUTH-SERVICE-FT-LOGIN | AuthService | 認証・JWT 発行・検証 | S: 認証ロジックのみ |
| DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT | EquipmentService | 備品 CRUD・貸出・返却のビジネスロジックと業務制約チェック | S: 備品業務ロジックのみ |
| DS-CL-USER-SERVICE-FT-MANAGE-BORROWER | UserService | 利用者 CRUD・初期管理者作成のビジネスロジックと業務制約チェック | S: 利用者業務ロジックのみ |
| DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID | DepartmentService | 部署名取得ビジネスロジック。クライアントを注入して None を「不明」に変換する | S: 部署名取得のみ |
| DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION | ReservationService | 予約 CRUD・競合チェック・ステータス更新のビジネスロジック | S: 予約業務ロジックのみ |
| DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY | EquipmentRepository | equipment テーブルの CRUD データアクセス | S: データ永続化のみ |
| DS-CL-USER-REPO-DT-BORROWER-ENTITY | UserRepository | user テーブルの CRUD データアクセス | S: データ永続化のみ |
| DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY | LoanStateRepository | loan_state テーブルの CRUD データアクセス | S: データ永続化のみ |
| DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY | ReservationRepository | reservation テーブルの CRUD データアクセス | S: データ永続化のみ |
| DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER | RealDepartmentClient | get_external_db_engine + fetch_department_name_by_login_id をクラスに包み MockDepartmentClient と同一インターフェースを提供する | S: 外部DB接続のみ |
| DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN | LoginView | ログイン画面コンポーネント | S: ログイン画面のみ |
| DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN | AdminEquipmentListView | 管理者向け備品一覧画面コンポーネント | S: 管理者備品一覧のみ |
| DS-CL-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN | EquipmentFormView | 備品登録・編集画面コンポーネント | S: 備品フォームのみ |
| DS-CL-EQUIPMENT-DELETE-VIEW-UI-EQUIPMENT-DELETE-CONFIRM-SCREEN | EquipmentDeleteConfirmView | 備品削除確認画面コンポーネント | S: 備品削除確認のみ |
| DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN | LoanFormView | 貸出登録画面コンポーネント | S: 貸出登録のみ |
| DS-CL-RETURN-CONFIRM-VIEW-UI-RETURN-CONFIRM-SCREEN | ReturnConfirmView | 返却確認画面コンポーネント | S: 返却確認のみ |
| DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN | UserListView | 利用者一覧画面コンポーネント | S: 利用者一覧のみ |
| DS-CL-USER-FORM-VIEW-UI-BORROWER-FORM-SCREEN | UserFormView | 利用者登録・編集画面コンポーネント | S: 利用者フォームのみ |
| DS-CL-USER-DELETE-VIEW-UI-BORROWER-DELETE-CONFIRM-SCREEN | UserDeleteConfirmView | 利用者削除確認画面コンポーネント | S: 利用者削除確認のみ |
| DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN | GeneralEquipmentListView | 一般利用者向け備品一覧画面コンポーネント | S: 一般利用者備品一覧のみ |
| DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN | ReservationCalendarView | 備品別予約詳細・カレンダー画面コンポーネント。予約一覧の「予約者名（部署）」表示は、各予約の user_login_id に対して DeptStore.fetchDeptName を呼び出して部署名を非同期取得する | S: 予約カレンダー画面のみ |
| DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN | ReservationFormView | 予約登録画面コンポーネント | S: 予約登録フォームのみ |
| DS-CL-AUTH-STORE-FT-LOGIN | AuthStore（Pinia） | ログイン状態・ロール・エラーメッセージの状態管理 | S: 認証状態管理のみ |
| DS-CL-EQUIPMENT-STORE-FT-VIEW-EQUIPMENT-LIST | EquipmentStore（Pinia） | 備品一覧データの状態管理 | S: 備品状態管理のみ |
| DS-CL-USER-STORE-FT-MANAGE-BORROWER | UserStore（Pinia） | 利用者一覧データの状態管理 | S: 利用者状態管理のみ |
| DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR | ReservationStore（Pinia） | 予約一覧データの状態管理 | S: 予約状態管理のみ |
| DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID | DeptStore（Pinia） | 部署名のキャッシュ管理と非同期取得 | S: 部署名キャッシュのみ |
| DS-CL-API-CLIENT-FT-VIEW-EQUIPMENT-LIST | ApiClient | axios 共通設定・401 インターセプター | S: HTTP 設定管理のみ。O: 新 API は関数追加のみで対応 |

**SOLID原則の適合状況:**

| 原則 | 適合 | 根拠 |
|---|---|---|
| S（単一責任） | 適合 | 全クラスが1つの責務のみを担う |
| O（開放閉鎖） | 適合 | ApiClient は新 API 追加時に関数追加のみで対応可能 |
| L（リスコフ置換） | 該当なし | 継承を使用しない |
| I（インターフェース分離） | 適合 | Router は Service の必要メソッドのみを呼び出す |
| D（依存関係逆転） | 適合 | Router → Service → Repository の一方向依存 |

### クラスの責務・主要属性・主要メソッド

#### DS-CL-AUTH-SERVICE-FT-LOGIN: AuthService

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | authenticate(login_id, password) → User | login_id でユーザーを検索し、bcrypt でパスワードを照合する。不一致は HTTPException(401) |
| メソッド | create_token(user) → str | role を含む JWT（有効期限60分）を生成して返す |
| メソッド | verify_token(token) → User | JWT を検証してユーザーを返す。期限切れ・不正は HTTPException(401) |

#### DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT: EquipmentService

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | list_equipment() → list[Equipment] | 全備品と対応する loan_state を結合して返す |
| メソッド | create(equipment_id, name) → Equipment | 備品を登録する |
| メソッド | update(equipment_id, name) → Equipment | 備品名を更新する |
| メソッド | delete(equipment_id) | status を確認し 'loaned' なら HTTPException(409)、それ以外は削除 |
| メソッド | loan(equipment_id, user_login_id, loan_date) | status が 'available' または 'reserved' でなければ HTTPException(409)。トランザクション内で loan_state 作成と status 更新 |
| メソッド | return_equipment(equipment_id) | loan_state がなければ HTTPException(404)。トランザクション内で loan_state 削除・期限切れ予約削除・残予約確認・status 更新 |

#### DS-CL-USER-SERVICE-FT-MANAGE-BORROWER: UserService

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | list_users() → list[User] | 全利用者一覧を返す |
| メソッド | create(display_name, login_id, password, role) → User | パスワードを bcrypt ハッシュ化して利用者を登録する |
| メソッド | update(login_id, display_name, password, role, requesting_login_id) → User | 最後の管理者の role 変更は HTTPException(409)。パスワードは入力があればハッシュ化して更新 |
| メソッド | delete(login_id, requesting_login_id) | 自分自身・最後の管理者・貸出中の貸出先の削除は HTTPException(409) |
| メソッド | initialize_admin(login_id, password) | user テーブルが空の場合のみ role=admin で利用者を作成する |
| メソッド | get_users_for_loan() → list[User] | 貸出登録画面の選択肢用に全利用者を返す |

#### DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID: DepartmentService

| 種別 | 名前 | 説明 |
|---|---|---|
| 属性 | _client | RealDepartmentClient または MockDepartmentClient（FastAPI Depends で注入） |
| メソッド | get_department_name(login_id: str) → str | _client.fetch_department_name_by_login_id(login_id) を呼び出す。None または例外発生時は "不明" を返す |

#### DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION: ReservationService

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | list_by_equipment(equipment_id: str) → list[Reservation] | 備品IDに紐づく全予約を開始日昇順で返す |
| メソッド | create(equipment_id, user_login_id, start_date, end_date) → Reservation | 重複チェック後に予約を登録する。equipment.status を 'reserved' に更新する（available 時のみ）。重複時は HTTPException(409) |
| メソッド | cancel(reservation_id, requesting_login_id, requesting_role) | 予約者本人または管理者以外は HTTPException(403)。削除後に残予約数を確認し equipment.status を更新する |

#### DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY: ReservationRepository

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | find_by_equipment_id(equipment_id: str) → list[Reservation] | 備品IDで全予約を取得 |
| メソッド | count_overlapping(equipment_id, start_date, end_date) → int | 期間重複件数をカウント |
| メソッド | create(data: ReservationCreate, user_login_id: str) → Reservation | 予約レコードを作成 |
| メソッド | find_by_id(reservation_id: str) → Optional[Reservation] | 予約IDで1件取得 |
| メソッド | delete(reservation_id: str) | 予約レコードを削除 |
| メソッド | count_by_equipment_id(equipment_id: str) → int | 備品の有効予約件数をカウント |
| メソッド | delete_expired_by_equipment(equipment_id: str, before_date: str) → None | end_date が before_date より前の予約レコードを全て削除する。返却処理時に呼び出す |

#### DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER: RealDepartmentClient

| 種別 | 名前 | 説明 |
|---|---|---|
| メソッド | __init__() | get_external_db_engine() でエンジンを生成して保持する |
| メソッド | fetch_department_name_by_login_id(login_id: str) → Optional[str] | fetch_department_name_by_login_id(engine, login_id) を呼び出して結果を返す |

**DeptStore の主要メソッド (DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID):**
- `fetchDeptName(loginId)` — GET /api/department/by-login-id を呼び出し、結果をキャッシュに保存する。同一 loginId の2回目以降の呼び出しはキャッシュから返す
- `fetchDeptNames(loginIds)` — 複数 loginId を並行呼び出し（Promise.all）して一括取得する

### クラス図

```mermaid
classDiagram
    class AuthRouter {
        +login(LoginRequest) LoginResponse
        +logout() Response
    }
    class EquipmentRouter {
        +list_equipment() list
        +create(EquipmentCreate) Equipment
        +update(id, EquipmentUpdate) Equipment
        +delete(id) Response
        +loan(id, LoanCreate) Equipment
        +return_equipment(id) Equipment
    }
    class UserRouter {
        +list_users() list
        +create(UserCreate) User
        +update(id, UserUpdate) User
        +delete(id) Response
    }
    class DepartmentRouter {
        +get_dept_name(login_id) DeptNameResponse
    }
    class ReservationRouter {
        +list_reservations(equipment_id) list
        +create(equipment_id, ReservationCreate) Reservation
        +cancel(reservation_id) Response
    }
    class AuthService {
        +authenticate(login_id, password) User
        +create_token(user) str
        +verify_token(token) User
    }
    class EquipmentService {
        +list_equipment() list
        +create(id, name) Equipment
        +update(id, name) Equipment
        +delete(id)
        +loan(id, user_id, date)
        +return_equipment(id)
    }
    class UserService {
        +list_users() list
        +create(name, id, pw, role) User
        +update(id, name, pw, role, req_id) User
        +delete(id, req_id)
        +initialize_admin(id, pw)
        +get_users_for_loan() list
    }
    class DepartmentService {
        -_client
        +get_department_name(login_id) str
    }
    class RealDepartmentClient {
        -_engine
        +fetch_department_name_by_login_id(login_id) Optional[str]
    }
    class MockDepartmentClient {
        +fetch_department_name_by_login_id(login_id) Optional[str]
    }
    class ReservationService {
        +list_by_equipment(equipment_id) list
        +create(equipment_id, user_login_id, start_date, end_date) Reservation
        +cancel(reservation_id, req_login_id, req_role)
    }
    class EquipmentRepository {
        +find_all() list
        +find_by_id(id) Equipment
        +create(data) Equipment
        +update(data) Equipment
        +delete(id)
    }
    class UserRepository {
        +find_all() list
        +find_by_login_id(id) User
        +count_admins() int
        +create(data) User
        +update(data) User
        +delete(id)
    }
    class LoanStateRepository {
        +find_by_equipment_id(id) LoanState
        +create(data) LoanState
        +delete_by_equipment_id(id)
        +exists_by_user_login_id(id) bool
    }
    class ReservationRepository {
        +find_by_equipment_id(id) list
        +count_overlapping(id, start, end) int
        +create(data, user_id) Reservation
        +find_by_id(id) Reservation
        +delete(id)
        +count_by_equipment_id(id) int
    }
    AuthRouter --> AuthService
    EquipmentRouter --> EquipmentService
    EquipmentRouter --> AuthService
    UserRouter --> UserService
    UserRouter --> AuthService
    DepartmentRouter --> DepartmentService
    DepartmentRouter --> AuthService
    DepartmentService --> RealDepartmentClient
    DepartmentService --> MockDepartmentClient
    ReservationRouter --> ReservationService
    ReservationRouter --> AuthService
    AuthService --> UserRepository
    EquipmentService --> EquipmentRepository
    EquipmentService --> LoanStateRepository
    UserService --> UserRepository
    UserService --> LoanStateRepository
    ReservationService --> ReservationRepository
    ReservationService --> EquipmentRepository
```

### システム内メッセージ一覧

| DS-ID | メッセージ名 | 内容 |
|---|---|---|
| DS-EV-LOGIN-REQUEST-FT-LOGIN | LoginRequest | login_id: str, password: str |
| DS-EV-LOGIN-RESPONSE-FT-LOGIN | LoginResponse | role: str, redirect_path: str |
| DS-EV-EQUIPMENT-CREATE-FT-MANAGE-EQUIPMENT | EquipmentCreate | equipment_id: str, name: str |
| DS-EV-EQUIPMENT-UPDATE-FT-MANAGE-EQUIPMENT | EquipmentUpdate | name: str |
| DS-EV-LOAN-CREATE-FT-LOAN-EQUIPMENT | LoanCreate | user_login_id: str, loan_date: str |
| DS-EV-USER-CREATE-FT-MANAGE-BORROWER | UserCreate | display_name: str, login_id: str, password: str, role: str |
| DS-EV-USER-UPDATE-FT-MANAGE-BORROWER | UserUpdate | display_name: str, password: str（省略可）, role: str |
| DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API | DeptNameResponse | department_name: str |
| DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION | ReservationCreate | start_date: str, end_date: str, user_login_id: Optional[str] |
| DS-EV-RESERVATION-RESPONSE-FT-VIEW-RESERVATION-CALENDAR | ReservationResponse | reservation_id: str, equipment_id: str, user_login_id: str, user_display_name: str, start_date: str, end_date: str |

### メッセージフロー図

```mermaid
sequenceDiagram
    participant F as フロントエンド
    participant R as Router
    participant S as Service
    participant Repo as Repository
    participant DB as SQLite

    Note over F,DB: ログイン処理
    F->>R: POST /api/auth/login (LoginRequest)
    R->>S: AuthService.authenticate()
    S->>Repo: UserRepository.find_by_login_id()
    Repo->>DB: SELECT
    DB-->>Repo: User row
    Repo-->>S: User
    S-->>R: User
    R->>S: AuthService.create_token()
    S-->>R: JWT token
    R-->>F: Set-Cookie(JWT) + LoginResponse

    Note over F,DB: 貸出処理
    F->>R: POST /api/equipment/{id}/loan (LoanCreate)
    R->>S: EquipmentService.loan()
    S->>Repo: EquipmentRepository.find_by_id()
    Repo->>DB: SELECT equipment
    DB-->>Repo: Equipment
    Repo-->>S: Equipment
    S->>Repo: LoanStateRepository.create() + EquipmentRepository.update()
    Repo->>DB: INSERT loan_state + UPDATE equipment（1トランザクション）
    DB-->>Repo: OK
    Repo-->>S: 完了
    S-->>R: Equipment（更新後）
    R-->>F: 200 OK
```

**外部DI設計 (DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID):**

FastAPI Depends を使い、環境変数 `MOCK_EXTERNAL_DB` の値に応じてクライアントを差し替える（core/external_department.py）。

| MOCK_EXTERNAL_DB 値 | 返却クライアント |
|---|---|
| "true" | MockDepartmentClient（mock/mock_department_client.py） |
| "false"（または未設定） | RealDepartmentClient（external/neon-department-db/src/department_client.py） |

---

## 6. その他設計

### エラーハンドリング設計

| DS-ID | HTTP ステータス | 発生条件 | レスポンス内容 |
|---|---|---|---|
| DS-FN-ERROR-401-FT-LOGIN | 401 Unauthorized | 未ログインでの API アクセス、または認証失敗 | {"detail": "認証が必要です"} |
| DS-FN-ERROR-403-FT-LOGIN | 403 Forbidden | 一般利用者が管理者専用 API を呼び出し | {"detail": "権限がありません"} |
| DS-FN-ERROR-404-FT-MANAGE-EQUIPMENT | 404 Not Found | 存在しない備品 ID・利用者 ID の指定 | {"detail": "対象が見つかりません"} |
| DS-FN-ERROR-409-FT-MANAGE-EQUIPMENT | 409 Conflict | 貸出中備品の削除、重複 ID 登録、削除不可利用者の削除 | {"detail": "操作できません：（理由）"} |
| DS-FN-ERROR-422-FT-MANAGE-EQUIPMENT | 422 Unprocessable Entity | 入力バリデーション失敗（空文字・型不正） | FastAPI デフォルトのバリデーションエラー形式 |
| DS-FN-ERROR-500-FT-MANAGE-EQUIPMENT | 500 Internal Server Error | 予期しないサーバーエラー | {"detail": "サーバーエラーが発生しました"} |
| DS-FN-ERROR-409-RESERVATION-CONFLICT-FT-MAKE-RESERVATION | 409 Conflict | 重複する予約期間への予約登録 | {"detail": "指定期間は既に予約されています"} |
| DS-FN-ERROR-403-RESERVATION-CANCEL-FT-CANCEL-RESERVATION | 403 Forbidden | 他の利用者の予約を一般利用者がキャンセル | {"detail": "権限がありません"} |
| DS-FN-ERROR-EXTERNAL-DB-DEPT-EX-FETCH-DEPARTMENT-MASTER | （HTTP ステータスなし） | 外部DB接続失敗・タイムアウト | DepartmentService が "不明" を返す。HTTP 200 で {"department_name": "不明"} を返却。他の操作は継続可能 |

フロントエンド側のエラー処理:

| DS-ID | 処理 | 実装箇所 |
|---|---|---|
| DS-FN-FRONTEND-401-HANDLER-FT-LOGIN | axios インターセプターで 401 を検知し、ログイン画面へリダイレクト | ApiClient |
| DS-FN-FRONTEND-ERROR-DISPLAY-FT-MANAGE-EQUIPMENT | 403/404/409/500 は Vuetify Snackbar でエラーメッセージを表示 | AuthStore.errorMessage |

### セキュリティ設計

| DS-ID | 設計項目 | 設計内容 |
|---|---|---|
| DS-FN-AUTH-JWT-FT-LOGIN | JWT 認証 | HS256 アルゴリズムで JWT を生成。秘密鍵は環境変数 JWT_SECRET_KEY から取得。有効期限 60 分 |
| DS-FN-AUTH-COOKIE-FT-LOGIN | Cookie セキュリティ | JWT を HttpOnly・SameSite=Strict に設定して送信。JavaScript からのアクセスを防ぐ |
| DS-FN-PASSWORD-HASH-NF-PASSWORD-HASH-STORAGE | パスワードハッシュ | bcrypt でパスワードをハッシュ化して保存。平文保存は行わない。画面への表示も行わない |
| DS-FN-ROLE-CHECK-NF-ROLE-BASED-AUTHORIZATION | ロール認可 | FastAPI Depends を使い、require_admin / get_current_user をルートごとに適用 |
| DS-FN-AUTO-LOGOUT-NF-SESSION-AUTO-LOGOUT-60MIN | 自動ログアウト | JWT 有効期限を 60 分に設定。フロントエンドは API から 401 を受信したらログイン画面へ遷移 |
| DS-FN-INPUT-VALIDATION-FT-MANAGE-EQUIPMENT | 入力バリデーション | Pydantic スキーマで全入力の型・必須・空文字不可チェック |
| DS-FN-EXTERNAL-DB-READONLY-NF-EXTERNAL-DB-READONLY | 外部DB書き込み禁止 | external/neon-department-db/src/department_client.py は SELECT のみ実行する。INSERT/UPDATE/DELETE を実行するコードを禁止する |
| DS-FN-EXTERNAL-DB-TIMEOUT-NF-EXTERNAL-DB-TIMEOUT | 外部DB接続タイムアウト | get_external_db_engine() の connect_args={"connect_timeout": 5} で5秒タイムアウトを設定する |
| DS-FN-EXTERNAL-DB-SECRET-EX-FETCH-DEPARTMENT-MASTER | 接続情報保護 | EXTERNAL_DB_URL は .env ファイルにのみ記載する。コードへの直書きを禁止する |

---

## 7. コード設計

### ディレクトリ構成

```
project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── core/
│   └── tests/
│       ├── unit/
│       └── integration/
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── api/
│   │   └── router/
│   └── nginx.conf
├── e2e/
│   └── tests/
└── docker-compose.yml
```

### ファイル一覧と役割

#### external/neon-department-db/src/

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| department_client.py | RealDepartmentClient クラスを含む（module-level 関数も維持） | DS-CL-REAL-DEPT-CLIENT-EX-FETCH-DEPARTMENT-MASTER |

#### backend/app/

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| main.py | FastAPI アプリ初期化、ルーター登録、起動時 DB 初期化と初期管理者作成 | DS-MD-BACKEND-FT-MANAGE-EQUIPMENT |
| core/config.py | 環境変数読み込み（JWT_SECRET_KEY・INITIAL_ADMIN_LOGIN_ID・INITIAL_ADMIN_PASSWORD・EXTERNAL_DB_URL・MOCK_EXTERNAL_DB） | DS-FN-AUTH-JWT-FT-LOGIN |
| core/auth.py | JWT 生成・検証・Depends 関数（get_current_user / require_admin） | DS-CL-AUTH-SERVICE-FT-LOGIN |
| core/database.py | SQLAlchemy エンジン・セッション生成 | DS-MD-DATABASE-DT-EQUIPMENT-ENTITY |
| core/external_department.py | 環境変数に応じて RealDepartmentClient / MockDepartmentClient を返す Depends ファクトリ | DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID |
| models/equipment.py | Equipment ORM モデル（equipment テーブル） | DS-SC-EQUIPMENT-DT-EQUIPMENT-ENTITY |
| models/user.py | User ORM モデル（user テーブル） | DS-SC-USER-DT-BORROWER-ENTITY |
| models/loan_state.py | LoanState ORM モデル（loan_state テーブル） | DS-SC-LOAN-STATE-DT-LOAN-STATE-ENTITY |
| models/reservation.py | Reservation ORM モデル（reservation テーブル） | DS-SC-RESERVATION-DT-RESERVATION-ENTITY |
| schemas/equipment.py | EquipmentCreate / EquipmentUpdate / EquipmentResponse | DS-EV-EQUIPMENT-CREATE-FT-MANAGE-EQUIPMENT |
| schemas/user.py | UserCreate / UserUpdate / UserResponse | DS-EV-USER-CREATE-FT-MANAGE-BORROWER |
| schemas/auth.py | LoginRequest / LoginResponse | DS-EV-LOGIN-REQUEST-FT-LOGIN |
| schemas/loan.py | LoanCreate | DS-EV-LOAN-CREATE-FT-LOAN-EQUIPMENT |
| schemas/reservation.py | ReservationCreate / ReservationResponse | DS-EV-RESERVATION-CREATE-FT-MAKE-RESERVATION |
| schemas/department.py | DeptNameResponse | DS-EV-DEPT-NAME-RESPONSE-FT-DEPT-NAME-API |
| repositories/equipment.py | EquipmentRepository | DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY |
| repositories/user.py | UserRepository | DS-CL-USER-REPO-DT-BORROWER-ENTITY |
| repositories/loan_state.py | LoanStateRepository | DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY |
| repositories/reservation.py | ReservationRepository | DS-CL-RESERVATION-REPO-DT-RESERVATION-ENTITY |
| services/auth_service.py | AuthService | DS-CL-AUTH-SERVICE-FT-LOGIN |
| services/equipment_service.py | EquipmentService | DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT |
| services/user_service.py | UserService | DS-CL-USER-SERVICE-FT-MANAGE-BORROWER |
| services/department_service.py | DepartmentService | DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID |
| services/reservation_service.py | ReservationService | DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION |
| api/auth.py | AuthRouter（POST /api/auth/login・logout） | DS-CL-AUTH-ROUTER-FT-LOGIN |
| api/equipment.py | EquipmentRouter（GET/POST/PUT/DELETE /api/equipment） | DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT |
| api/users.py | UserRouter（GET/POST/PUT/DELETE /api/users） | DS-CL-USER-ROUTER-FT-MANAGE-BORROWER |
| api/department.py | DepartmentRouter（GET /api/department/by-login-id） | DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API |
| api/reservations.py | ReservationRouter（GET・POST /api/equipment/{id}/reservations、DELETE /api/reservations/{id}） | DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION |

#### frontend/src/

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| views/LoginView.vue | ログイン画面 | DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN |
| views/AdminEquipmentListView.vue | 管理者向け備品一覧画面 | DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN |
| views/EquipmentFormView.vue | 備品登録・編集画面（新規・編集共用） | DS-CL-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN |
| views/EquipmentDeleteConfirmView.vue | 備品削除確認画面 | DS-CL-EQUIPMENT-DELETE-VIEW-UI-EQUIPMENT-DELETE-CONFIRM-SCREEN |
| views/LoanFormView.vue | 貸出登録画面 | DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN |
| views/ReturnConfirmView.vue | 返却確認画面 | DS-CL-RETURN-CONFIRM-VIEW-UI-RETURN-CONFIRM-SCREEN |
| views/UserListView.vue | 利用者一覧画面 | DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN |
| views/UserFormView.vue | 利用者登録・編集画面（新規・編集共用） | DS-CL-USER-FORM-VIEW-UI-BORROWER-FORM-SCREEN |
| views/UserDeleteConfirmView.vue | 利用者削除確認画面 | DS-CL-USER-DELETE-VIEW-UI-BORROWER-DELETE-CONFIRM-SCREEN |
| views/GeneralEquipmentListView.vue | 一般利用者向け備品一覧画面 | DS-CL-GENERAL-EQUIPMENT-LIST-VIEW-UI-GENERAL-EQUIPMENT-LIST-SCREEN |
| views/ReservationCalendarView.vue | 備品別予約詳細・カレンダー画面 | DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN |
| views/ReservationFormView.vue | 予約登録画面 | DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN |
| stores/auth.js | AuthStore（Pinia）：ログイン状態・ロール・エラーメッセージ | DS-CL-AUTH-STORE-FT-LOGIN |
| stores/equipment.js | EquipmentStore（Pinia）：備品一覧データ | DS-CL-EQUIPMENT-STORE-FT-VIEW-EQUIPMENT-LIST |
| stores/user.js | UserStore（Pinia）：利用者一覧データ | DS-CL-USER-STORE-FT-MANAGE-BORROWER |
| stores/reservation.js | ReservationStore（Pinia）：予約一覧データ | DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR |
| stores/dept.js | DeptStore（Pinia）：部署名キャッシュ管理 | DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID |
| api/client.js | axios 共通設定・401 インターセプター | DS-CL-API-CLIENT-FT-VIEW-EQUIPMENT-LIST |
| api/auth.js | 認証 API コール関数（login / logout） | DS-CL-AUTH-ROUTER-FT-LOGIN |
| api/equipment.js | 備品 API コール関数（list / create / update / delete / loan / return） | DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT |
| api/users.js | 利用者 API コール関数（list / create / update / delete） | DS-CL-USER-ROUTER-FT-MANAGE-BORROWER |
| api/department.js | 部署名取得 API コール関数 | DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API |
| api/reservations.js | 予約 API コール関数 | DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION |
| router/index.js | Vue Router 定義（ログインガード・ロール別ルート） | DS-CL-AUTH-STORE-FT-LOGIN |

**Vue Router ルート定義（DS-CL-AUTH-STORE-FT-LOGIN）:**

| パス | View | 権限ガード |
|---|---|---|
| /login | LoginView | なし（未ログイン時のみアクセス可） |
| /admin/equipment | AdminEquipmentListView | admin のみ |
| /admin/equipment/new | EquipmentFormView | admin のみ |
| /admin/equipment/:id/edit | EquipmentFormView | admin のみ |
| /admin/equipment/:id/delete | EquipmentDeleteConfirmView | admin のみ |
| /admin/equipment/:id/loan | LoanFormView | admin のみ |
| /admin/equipment/:id/return | ReturnConfirmView | admin のみ |
| /admin/users | UserListView | admin のみ |
| /admin/users/new | UserFormView | admin のみ |
| /admin/users/:id/edit | UserFormView | admin のみ |
| /admin/users/:id/delete | UserDeleteConfirmView | admin のみ |
| /general/equipment | GeneralEquipmentListView | general のみ |
| /equipment/:id/reservations | ReservationCalendarView | 要ログイン（全ロール） |
| /equipment/:id/reservations/new | ReservationFormView | 要ログイン（全ロール） |
| / | リダイレクト | ログイン状態と role に応じて /admin/equipment または /general/equipment へ |

#### e2e/

| ファイル名 | 役割 | DS-ID |
|---|---|---|
| tests/auth.spec.js | ログイン・ログアウト・自動ログアウト E2E テスト | DS-MD-E2E-TEST-TS-VERIFY-ADMIN-LOGIN |
| tests/equipment.spec.js | 備品管理・貸出・返却 E2E テスト | DS-MD-E2E-TEST-TS-VERIFY-EQUIPMENT-MANAGEMENT |
| tests/users.spec.js | 利用者管理 E2E テスト | DS-MD-E2E-TEST-TS-VERIFY-BORROWER-MANAGEMENT |
| tests/general.spec.js | 一般利用者閲覧 E2E テスト | DS-MD-E2E-TEST-TS-VERIFY-GENERAL-EQUIPMENT-VIEW |
| tests/reservations.spec.js | 予約 CRUD・競合チェック・キャンセル E2E テスト | DS-FN-E2E-RESERVATION-CREATE-TS-VERIFY-RESERVATION-CREATE |
| tests/department.spec.js | 部署名非同期表示 E2E テスト | DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL |
| playwright.config.js | Playwright 設定（URL: http://frontend、タイムアウト等） | DS-MD-E2E-TEST-TS-VERIFY-ADMIN-LOGIN |

### コーディング規約

#### バックエンド（Python）

| 項目 | 規約 |
|---|---|
| 命名規則 | 変数・関数は snake_case、クラスは PascalCase |
| 型ヒント | 全関数の引数と戻り値に型ヒントを付与する |
| 依存注入 | FastAPI Depends を使い Service と Repository を注入する |
| 例外 | HTTPException（FastAPI）で統一する |
| DB 操作 | SQLAlchemy ORM を使用する。生 SQL は禁止 |

#### フロントエンド（Vue 3 / JavaScript）

| 項目 | 規約 |
|---|---|
| 命名規則 | コンポーネントは PascalCase、変数・関数は camelCase |
| API 呼び出し | api/ 配下の関数のみを使用する。View から直接 axios を呼び出すことを禁止する |
| 状態管理 | Pinia ストアを経由してデータを操作する |
| エラー表示 | Vuetify Snackbar コンポーネントを AuthStore.errorMessage で制御する |

---

## 8. テスト設計

### テスト種別と方針

| テスト種別 | 目的 | 方法 |
|---|---|---|
| 単体テスト | Service 層・Repository 層の個別ロジックと業務制約チェック | pytest + SQLite on-memory DB |
| 結合テスト | 全 API エンドポイントの入出力・認可・エラー検証 | pytest + FastAPI TestClient |
| E2E テスト | 要件定義書の全テスト用利用シナリオの画面操作検証 | Playwright |

### 単体テスト一覧

| DS-ID | テスト対象 | 正常系 | 異常系 |
|---|---|---|---|
| DS-FN-TEST-AUTH-AUTHENTICATE-FT-LOGIN | AuthService.authenticate | 正しい ID/PW で User を返す | 存在しない ID → 401、誤り PW → 401 |
| DS-FN-TEST-AUTH-TOKEN-FT-LOGIN | AuthService.create_token / verify_token | トークン生成・検証成功 | 期限切れ・改ざんトークン → 401 |
| DS-FN-TEST-EQUIPMENT-CREATE-FT-MANAGE-EQUIPMENT | EquipmentService.create | 備品登録成功 | 重複 ID → 409 |
| DS-FN-TEST-EQUIPMENT-DELETE-FT-MANAGE-EQUIPMENT | EquipmentService.delete | 貸出可能備品の削除成功 | 貸出中備品の削除 → 409 |
| DS-FN-TEST-EQUIPMENT-LOAN-FT-LOAN-EQUIPMENT | EquipmentService.loan | 貸出可能備品の貸出成功。status='reserved' でも貸出成功 | 貸出中備品の再貸出 → 409 |
| DS-FN-TEST-EQUIPMENT-RETURN-FT-RETURN-EQUIPMENT | EquipmentService.return_equipment | 貸出中備品の返却成功。残予約あり → status='reserved'。残予約なし → status='available'。end_date < 返却日の予約が自動削除される | loan_state なし → 404 |
| DS-FN-TEST-USER-CREATE-FT-MANAGE-BORROWER | UserService.create | 利用者登録成功、パスワードがハッシュ化される | 重複 login_id → 409 |
| DS-FN-TEST-USER-DELETE-FT-MANAGE-BORROWER | UserService.delete | 削除可能利用者の削除成功 | 自分自身・最後の管理者・貸出中貸出先 → 409 |
| DS-FN-TEST-USER-LAST-ADMIN-FT-MANAGE-BORROWER | UserService.update | 管理者が2人いる場合の role 変更成功 | 最後の管理者の role を general に変更 → 409 |
| DS-FN-TEST-INIT-ADMIN-OP-INITIAL-ADMIN-ENV | UserService.initialize_admin | テーブル空時に role=admin で作成 | テーブル非空時はスキップ（何もしない） |
| DS-FN-TEST-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID | DepartmentService.get_department_name | クライアントが部署名を返す → そのまま返す | クライアントが None を返す → "不明"。クライアントが例外を送出 → "不明" |
| DS-FN-TEST-RESERVATION-CREATE-FT-MAKE-RESERVATION | ReservationService.create | 重複なし → 予約作成成功・equipment.status 更新 | 重複あり → 409。equipment が存在しない → 404 |
| DS-FN-TEST-RESERVATION-CANCEL-FT-CANCEL-RESERVATION | ReservationService.cancel | 本人がキャンセル成功・残予約0件→status=available | 他人がキャンセル → 403。管理者がキャンセル成功。残予約あり → status=reserved |
| DS-FN-TEST-RESERVATION-CONFLICT-NF-RESERVATION-CONFLICT-PREVENTION | ReservationRepository.count_overlapping | 重複なし → 0。前後接触（境界）→ 0 | 1日重複 → 1。完全包含 → 1 |

### 結合テスト一覧

| DS-ID | テスト対象 | 正常系 | 異常系 |
|---|---|---|---|
| DS-FN-TEST-API-LOGIN-FT-LOGIN | POST /api/auth/login | ログイン成功・Cookie セット・role 返却 | 認証失敗 → 401 |
| DS-FN-TEST-API-EQUIPMENT-LIST-FT-VIEW-EQUIPMENT-LIST | GET /api/equipment | ログイン済みで一覧取得 | 未ログイン → 401 |
| DS-FN-TEST-API-EQUIPMENT-CRUD-FT-MANAGE-EQUIPMENT | POST/PUT/DELETE /api/equipment | 管理者が CRUD 成功 | 一般利用者が実行 → 403 |
| DS-FN-TEST-API-LOAN-FT-LOAN-EQUIPMENT | POST /api/equipment/{id}/loan | 貸出成功・status が loaned になる | 貸出中備品 → 409、一般利用者 → 403 |
| DS-FN-TEST-API-RETURN-FT-RETURN-EQUIPMENT | POST /api/equipment/{id}/return | 返却成功・status が available または reserved になる | loan_state なし → 404 |
| DS-FN-TEST-API-USER-CRUD-FT-MANAGE-BORROWER | GET/POST/PUT/DELETE /api/users | 管理者が CRUD 成功 | 一般利用者が実行 → 403 |
| DS-FN-TEST-API-DEPT-NAME-FT-DEPT-NAME-API | GET /api/department/by-login-id | ログイン済みで200・部署名返却（モッククライアント） | 未ログイン → 401 |
| DS-FN-TEST-API-RESERVATION-CRUD-FT-MAKE-RESERVATION | GET/POST /api/equipment/{id}/reservations、DELETE /api/reservations/{id} | 予約一覧取得・予約作成・キャンセル成功 | 重複期間 → 409。他人キャンセル → 403。一般利用者が他人のIDで予約作成 → 403 |

### E2E テスト

要件定義書の RQ-TS-* を 100% 網羅する。詳細はセクション 11 を参照。

---

## 9. 運用設計

### docker compose 構成

| サービス名 | イメージ | 役割 | ポート |
|---|---|---|---|
| frontend | Nginx + Vue3 マルチステージビルド成果物 | Vue3 SPA 配信・/api/ プロキシ | 80:80 |
| backend | Python 3.12 + uvicorn | FastAPI アプリ | 8000（非公開） |

SQLite ファイルは backend コンテナ内の `/app/data/app.db` にホストのボリュームをマウントして永続化する。

backend サービスの環境変数:

| 変数名 | 説明 |
|---|---|
| JWT_SECRET_KEY | JWT 署名秘密鍵 |
| INITIAL_ADMIN_LOGIN_ID | 初期管理者ログインID |
| INITIAL_ADMIN_PASSWORD | 初期管理者パスワード |
| EXTERNAL_DB_URL | Neon PostgreSQL 接続文字列（real モード時に必須） |
| MOCK_EXTERNAL_DB | "true" で MockDepartmentClient を使用する。デフォルト "false" |

external/neon-department-db ディレクトリを backend コンテナに `/app/external/neon-department-db` としてマウントする。PYTHONPATH に `/app/external/neon-department-db` を追加する。

### 初期化設計

- backend コンテナ起動時に自動で SQLAlchemy create_all を実行して DB スキーマを作成する（reservation テーブルを含む）
- 環境変数 `INITIAL_ADMIN_LOGIN_ID` と `INITIAL_ADMIN_PASSWORD` を設定した状態で初回起動すると、user テーブルが空の場合のみ初期管理者を作成する
- 以降の起動では user テーブルが空でない限りスキップされる

### 起動方法

README.md に以下の内容を記載する:

1. プロジェクトルートに `.env` ファイルを作成し `INITIAL_ADMIN_LOGIN_ID`・`INITIAL_ADMIN_PASSWORD`・`JWT_SECRET_KEY` を設定する
2. real モードで外部DB連携を使う場合は `EXTERNAL_DB_URL` を設定する。ローカル開発時は `MOCK_EXTERNAL_DB=true` を設定することで外部DBなしで起動できる
3. `docker compose up -d` で起動する
4. ブラウザで `http://localhost` にアクセスする

`.env` 設定例:
```
EXTERNAL_DB_URL=postgresql://user:password@host/db?sslmode=require&channel_binding=require
MOCK_EXTERNAL_DB=false
```

mock モードで起動する場合は `MOCK_EXTERNAL_DB=true` に設定する（EXTERNAL_DB_URL は不要）。

---

## 10. ログ・監視・アラート設計

### ログ設計

業務上の操作ログ（貸出・返却・備品編集・利用者編集）は設計しない（RQ-OP-NO-BUSINESS-OPERATION-LOG）。アプリ起動ログ・初期管理者作成ログ（INFO）・エラーログ（ERROR）は uvicorn のデフォルトログ出力のみを使用する。追加のログ設計は不要。

### 監視・アラート設計

業務上の監視・アラートは設計しない（RQ-OP-NO-BUSINESS-ALERT）。

---

## 11. E2Eテスト設計

### docker compose test_playwright サービス定義

```yaml
test_playwright:
  image: mcr.microsoft.com/playwright:v1.59.0
  profiles:
    - test
    - mock
    - real
  volumes:
    - ./e2e:/e2e
  working_dir: /e2e
  depends_on:
    - frontend
    - backend
  environment:
    - BASE_URL=http://frontend

backend:
  environment:
    - MOCK_EXTERNAL_DB=${MOCK_EXTERNAL_DB:-true}
    - EXTERNAL_DB_URL=${EXTERNAL_DB_URL:-}
```

プロファイル `mock`（デフォルト CI）: `MOCK_EXTERNAL_DB=true`
プロファイル `real`（手動実行）: `MOCK_EXTERNAL_DB=false` + `EXTERNAL_DB_URL` 設定済み

### E2E 実行コマンド

**mock モード（CI 必須）:**
```
MOCK_EXTERNAL_DB=true docker compose run --rm test_playwright sh -c "npm install && npx playwright test"
```

**real モード（手動のみ）:**
```
MOCK_EXTERNAL_DB=false docker compose run --rm test_playwright sh -c "npm install && npx playwright test"
```

### E2Eシナリオ一覧

| DS-ID | 対応 RQ-TS | 目的 | 前提条件 | 手順 | 期待結果 | モード |
|---|---|---|---|---|---|---|
| DS-FN-E2E-ADMIN-LOGIN-TS-VERIFY-ADMIN-LOGIN | RQ-TS-VERIFY-ADMIN-LOGIN | 管理者ログイン成功を確認する | 初期管理者が作成済み | ログイン画面で管理者のログインIDとパスワードを入力してログインボタンを押す | 管理者向け備品一覧画面に遷移し、備品登録ボタンと利用者管理ボタンが表示される | mock / real |
| DS-FN-E2E-GENERAL-LOGIN-TS-VERIFY-GENERAL-LOGIN | RQ-TS-VERIFY-GENERAL-LOGIN | 一般利用者ログイン成功を確認する | 一般利用者が登録済み | ログイン画面で一般利用者のログインIDとパスワードを入力してログインボタンを押す | 一般利用者向け備品一覧画面に遷移し、操作ボタンが表示されない | mock / real |
| DS-FN-E2E-INIT-ADMIN-TS-VERIFY-INITIAL-ADMIN-CREATION | RQ-TS-VERIFY-INITIAL-ADMIN-CREATION | 初期管理者の自動作成を確認する | 環境変数設定済み・DB は空 | アプリを起動し、環境変数の ID とパスワードでログインする | 管理者向け備品一覧画面に遷移する | mock / real |
| DS-FN-E2E-EQUIPMENT-MANAGEMENT-TS-VERIFY-EQUIPMENT-MANAGEMENT | RQ-TS-VERIFY-EQUIPMENT-MANAGEMENT | 備品の登録・編集・削除・貸出中削除不可を確認する | 管理者でログイン済み | 備品登録→備品名編集→貸出可能備品を削除→貸出中備品の削除を試みる | 登録・編集・削除が成功する。貸出中備品の削除はエラーが表示される | mock / real |
| DS-FN-E2E-BORROWER-MANAGEMENT-TS-VERIFY-BORROWER-MANAGEMENT | RQ-TS-VERIFY-BORROWER-MANAGEMENT | 利用者の登録・編集・削除・制限を確認する | 管理者でログイン済み | 利用者登録→権限変更→削除可能利用者を削除→自分自身・最後の管理者・貸出中貸出先の削除を試みる | 登録・編集・削除が成功する。制限対象の操作はエラーが表示される | mock / real |
| DS-FN-E2E-LOAN-EQUIPMENT-TS-VERIFY-LOAN-EQUIPMENT | RQ-TS-VERIFY-LOAN-EQUIPMENT | 貸出記録を確認する | 管理者でログイン済み、貸出可能備品と利用者が存在する | 管理者向け備品一覧から貸出可能備品を選択し、貸出登録画面で利用者と貸出日を入力して登録する | 備品状態が貸出中になり、一覧に貸出先利用者名と貸出日が表示される | mock / real |
| DS-FN-E2E-RETURN-EQUIPMENT-TS-VERIFY-RETURN-EQUIPMENT | RQ-TS-VERIFY-RETURN-EQUIPMENT | 返却処理を確認する | 管理者でログイン済み、貸出中備品が存在する | 管理者向け備品一覧から貸出中備品を選択し、返却確認画面で内容を確認して返却を実行する | 備品状態が貸出可能になり、貸出先と貸出日が表示されなくなる | mock / real |
| DS-FN-E2E-GENERAL-VIEW-TS-VERIFY-GENERAL-EQUIPMENT-VIEW | RQ-TS-VERIFY-GENERAL-EQUIPMENT-VIEW | 一般利用者閲覧専用を確認する | 一般利用者でログイン済み、備品が存在する | 一般利用者向け備品一覧画面を開く | 全備品の状態が表示され、登録・貸出・返却・削除ボタンが表示されない | mock / real |
| DS-FN-E2E-LOGOUT-TS-VERIFY-LOGOUT | RQ-TS-VERIFY-LOGOUT | ログアウトを確認する | 任意の利用者でログイン済み | ログアウトボタンを押す | ログイン画面に遷移し、管理者画面への再アクセス時に再ログインが要求される | mock / real |
| DS-FN-E2E-AUTO-LOGOUT-TS-VERIFY-AUTO-LOGOUT | RQ-TS-VERIFY-AUTO-LOGOUT | 未操作60分の自動ログアウトを確認する | 任意の利用者でログイン済み | ログイン後、Playwright の page.clock.fastForward で 60 分経過させた後に操作する | セッションが切れ、ログイン画面に遷移する | mock / real |
| DS-FN-E2E-DEPT-DISPLAY-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL | RQ-TS-VERIFY-DEPT-DISPLAY-FROM-EXTERNAL | 画面即時表示後に非同期で部署名が取得・表示されること | 管理者ログイン済み。login_id が demo_users に存在する利用者が登録済み | 1. 利用者一覧画面を開く 2. 初期表示で部署列が「取得中...」であることを確認 3. 取得完了後の表示を確認 | 2. 画面本体は即時表示される 3.「取得中...」が部署名に置き換わる | mock / real |
| DS-FN-E2E-DEPT-LOAN-TS-VERIFY-DEPT-DISPLAY-IN-LOAN | RQ-TS-VERIFY-DEPT-DISPLAY-IN-LOAN | 貸出登録画面のドロップダウンに部署名が表示されること | 管理者ログイン済み | 1. 在庫備品の「貸出」ボタンを押す 2. 貸出登録画面のドロップダウンを確認 | 「利用者名（部署名）」形式で選択肢が表示される | mock / real |
| DS-FN-E2E-DEPT-EQUIPMENT-LIST-TS-VERIFY-DEPT-DISPLAY-IN-EQUIPMENT-LIST | RQ-TS-VERIFY-DEPT-DISPLAY-IN-EQUIPMENT-LIST | 管理者向け備品一覧の貸出先に部署名が表示されること | 管理者ログイン済み、貸出中備品が存在する | 1. 管理者向け備品一覧を開く | 貸出中備品行に「利用者名（部署名）」が表示される | mock / real |
| DS-FN-E2E-RESERVATION-CREATE-TS-VERIFY-RESERVATION-CREATE | RQ-TS-VERIFY-RESERVATION-CREATE | 一般利用者が備品を期間指定で予約できること | 一般利用者ログイン済み、在庫備品が存在する | 1.「予約状況」ボタンを押す 2. カレンダー画面で「予約する」を押す 3. 開始日・終了日を入力して登録する | カレンダーに予約期間がハイライト表示される。備品一覧のステータスが「予約済み」になる | mock / real |
| DS-FN-E2E-RESERVATION-CONFLICT-TS-VERIFY-RESERVATION-CONFLICT | RQ-TS-VERIFY-RESERVATION-CONFLICT | 重複する期間の予約が拒否されること | 一般利用者ログイン済み、対象備品に 2026-06-01〜2026-06-05 の予約が存在する | 1. 同じ備品に 2026-06-03〜2026-06-07 の期間で予約を試みる | 「指定期間は既に予約されています」が表示され、予約が登録されない | mock / real |
| DS-FN-E2E-RESERVATION-NON-OVERLAP-TS-VERIFY-RESERVATION-NON-OVERLAP | RQ-TS-VERIFY-RESERVATION-NON-OVERLAP | 重複しない期間の複数予約が許可されること | 一般利用者ログイン済み、対象備品に 2026-06-01〜2026-06-05 の予約が存在する | 1. 同じ備品に 2026-06-10〜2026-06-15 の期間で予約を試みる | 予約が正常に登録される。カレンダーに両方の期間がハイライト表示される | mock / real |
| DS-FN-E2E-RESERVATION-CANCEL-TS-VERIFY-RESERVATION-CANCEL | RQ-TS-VERIFY-RESERVATION-CANCEL | 予約者本人が自分の予約をキャンセルできること | 一般利用者ログイン済み、当該利用者の予約が存在する | 1.「予約状況」ボタンを押す 2. 自分の予約行の「キャンセル」ボタンを押す | カレンダーから該当予約が消える。他に予約がなければ備品ステータスが「在庫」になる | mock / real |
| DS-FN-E2E-ADMIN-CANCEL-RESERVATION-TS-VERIFY-ADMIN-CANCEL-OTHERS-RESERVATION | RQ-TS-VERIFY-ADMIN-CANCEL-OTHERS-RESERVATION | 管理者が他利用者の予約をキャンセルできること | 管理者ログイン済み、他の利用者の予約が存在する | 1. 該当備品の「予約状況」ボタンを押す 2. 他の利用者の予約行の「キャンセル」ボタンを押す | 該当予約がカレンダーから消える | mock / real |
| DS-FN-E2E-RESERVATION-TO-LOAN-TS-VERIFY-RESERVATION-TO-LOAN | RQ-TS-VERIFY-RESERVATION-TO-LOAN | 予約済み備品に対して管理者が貸出操作でき、返却時に期間終了済み予約が自動削除されること | 管理者ログイン済み、予約済み状態の備品が存在する | 1. 備品一覧の「貸出」ボタンを押す 2. 貸出登録画面で利用者を選択して登録する 3. 備品を返却する | 2. 備品ステータスが「貸出中」になる 3. end_date が返却日より前の予約が自動削除される。残予約がなければ備品ステータスが「在庫」になる | mock / real |
| DS-FN-E2E-EXTERNAL-DB-FAILURE-TS-VERIFY-EXTERNAL-DB-FAILURE | RQ-TS-VERIFY-EXTERNAL-DB-FAILURE | 外部DB接続失敗時に部署名が「不明」と表示されること | 外部DBが接続不可の状態（MOCK_EXTERNAL_DB=false かつ EXTERNAL_DB_URL に無効な値） | 1. 利用者一覧画面を開く | 部署名欄に「不明」が表示される。他の画面表示・操作は継続可能 | real |

### E2E 運用設計

- テスト資産はプロジェクトルート `e2e/` 配下に配置する
- 外部モックは `external/neon-department-db/mock/` を正本とし、`e2e/external/neon-department-db/mock` からシンボリックリンクで参照する。シンボリックリンクは Git 管理下に置く
- CI 必須ゴールは `mock` モード E2E 全件通過（`MOCK_EXTERNAL_DB=true`）
- `real` モード E2E は手動実行のみ必須
- テスト実行時の URL は docker compose 内サービス名 `http://frontend` を使用する
- 自動ログアウトテストは Playwright の `page.clock.fastForward` を使い 60 分相当の時間を進めてテストする
- テスト失敗時は修正と再実行を繰り返し、全シナリオ通過まで継続する

---

## 12. 削除可能な設計要素の確認

MVP 設計として以下の要素は設計対象外とした。追加すると要件を超えるため設計に含めない。

| 削除した設計要素 | 理由 |
|---|---|
| 返却予定日管理ロジック | RQ-BZ の対象外として要件で除外済み |
| 貸出履歴テーブル | 現在の貸出状態のみ管理するため不要 |
| 検索・フィルター API | 最大100件で全件表示で要件を満たすため不要 |
| 備品詳細画面 | 一覧と登録・編集画面で情報が揃うため不要 |
| 利用者詳細画面 | 一覧と登録・編集画面で情報が揃うため不要 |
| Redis セッションストア | JWT + SQLite で小規模要件を満たすため不要 |
| CSRF トークン | JWT を HTTP-only Cookie で管理し SameSite=Strict を設定するため追加 CSRF 対策は不要 |
| 部署一覧取得 API（全件取得） | RQ-FT-SELECT-DEPARTMENT が削除されたため不要。ログインIDによる1件取得のみで要件を満たす |
| 利用者フォームへの部署選択フィールド | 外部DB動的取得に変更したため不要 |
| 予約更新（PATCH）API | 修正はキャンセル→再登録で対応するため Update は設計しない |

# 変更設計書: アカウントの管理（段 3）

正本: `docs/detail_design.md`（段 1・2 の詳細設計書）。この文書は正本を書き換えず、変更する設計要素だけを [追加] か [変更] で書く。
変更要件: `change_requirements.md`。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存の詳細設計書 1 章（Python 3.12、Flask、waitress、SQLite の標準ライブラリ）を使う。新しいライブラリは足さない。

## 2. システム構成

変更なし。既存の詳細設計書 2 章のとおり。

## 3. データ設計

### 3-1. データモデル

変更なし（テーブルと列は増やさない）。アカウントの行の役割（`role`）は、担当者（`manager`）か社員（`member`）。削除は行の物理削除で、削除の記録を残す表は作らない（`RQ-DT-ACCOUNT-HARD-DELETE`）。貸出の記録（`loans`）は `account_id` で社員を指すため、借りている社員は削除の前に確かめる（`RQ-FT-NO-DELETE-BORROWING-ACCOUNT`）。

### 3-2. トランザクションと排他制御

[追加] 役割の変更・パスワードの再設定・削除は、書き込みのトランザクションを先に開き（`BEGIN IMMEDIATE`）、対象の行の確認と更新を同じ区切りで行う。担当者の人数の確認（`RQ-FT-KEEP-ONE-MANAGER`）と、借りている貸出の確認（`RQ-FT-NO-DELETE-BORROWING-ACCOUNT`）も同じトランザクションの中で行い、同時の操作で担当者が 0 人になったり、借りている社員が削除されたりしないようにする。

### 3-3. 状態遷移

[追加] アカウントの役割: 社員 → 担当者（担当者にする）、担当者 → 社員（担当者から外す。担当者が 2 人以上のときだけ）。アカウントの存在: 有 → 無（削除。借りていない社員で、担当者が 1 人だけでない場合だけ）。

## 4. アーキテクチャ設計

### 4-1. 外部設計

[追加] 利用者向けインターフェース:

- アカウントの一覧（`DS-IF-ACCOUNT-LIST-SCREEN`）: パス `/accounts/`。担当者だけ。表（`tbody tr`、各行に `data-employee-number`）の列は社員番号、名前、「担当者」か「社員」、操作。操作のボタンは「担当者にする」「担当者から外す」「パスワード再設定」「削除」。貸出状況の画面（`DS-IF-LOAN-STATUS-SCREEN`）に担当者だけに出すリンク「アカウントの一覧」を追加する。
- パスワードの再設定（同じ画面）: パス `/accounts/<社員番号>/password/`。GET で、その行を開いた一覧を表示する（`input[name=new_password]` と「確定」）。POST で再設定し、成功したら一覧へ戻して `.message` に「パスワードを再設定しました」を出す。短いときはその行の `.field-error` に「パスワードは 8 文字以上で入力してください」を出し、一覧を再表示する（新しいパスワードの入力は残さない）。
- 役割の変更: パス `/accounts/<社員番号>/role/`（POST。フォームの値 `role` は `manager` か `member`）。成功は `.message` に「担当者にしました」か「担当者から外しました」。
- 削除: パス `/accounts/<社員番号>/delete/`（POST）。成功は `.message` に「アカウントを削除しました」。

知らせの文言（追加分）:

| 場面 | 出し方 | 文言 |
|---|---|---|
| 担当者以外が操作・閲覧 | 貸出状況の画面へ戻し `.message` | この操作は担当者だけが行えます（既存の文言） |
| 借りている社員の削除 | 一覧の `.message` | この社員は備品を借りているため削除できません。先に返却を処理してください |
| 担当者が 1 人だけ（外す・削除） | 一覧の `.message` | 担当者が 1 人もいなくなるため、この操作はできません |
| 対象のアカウントが無い | 一覧の `.message` | アカウントが見つかりません |
| 役割の変更・再設定・削除の成功 | 一覧の `.message` | 担当者にしました／担当者から外しました／パスワードを再設定しました／アカウントを削除しました |

インターフェース仕様（追加分）:

| 画面 / 操作 | 入力とバリデーション | 出力 | エラー仕様 |
|---|---|---|---|
| アカウントの一覧（GET `/accounts/`） | なし | 全アカウントを社員番号の昇順に並べた表（担当者か社員か） | 担当者以外は貸出状況へ戻し `.message`。未ログインはログイン画面へ |
| パスワードの再設定（GET・POST `/accounts/<社員番号>/password/`） | 新しいパスワード: 8 文字以上（`DS-FN-VALIDATE-PASSWORD`） | 成功: 一覧へ移動し「パスワードを再設定しました」 | 短いときは、その行の `.field-error`。対象が無ければ一覧へ戻し「アカウントが見つかりません」 |
| 役割の変更（POST `/accounts/<社員番号>/role/`） | 役割は `manager` か `member` のみ | 成功: 一覧へ移動し成功の知らせ | 担当者が 1 人だけで外す → 「担当者が 1 人もいなくなるため、この操作はできません」 |
| 削除（POST `/accounts/<社員番号>/delete/`） | なし（画面では確認ダイアログで「はい」のときだけ送る） | 成功: 一覧へ移動し「アカウントを削除しました」 | 借りている社員 → 削除しない。担当者が 1 人だけ → 削除しない |

外部システム連携: 無し。

### 4-2. 内部設計

[変更] 処理フロー（リクエストごと）: 利用者の判定は、セッションに入った利用者の社員番号ではなく、要求ごとに DB のアカウントを引き直す（`DS-FN-LOAD-CURRENT-USER`）。
1. セッションが無い → 未ログイン。
2. 制限時間を超えた → セッションを消して未ログイン（既存どおり）。
3. アカウントが DB に無い（削除された）→ セッションを消して未ログイン。
4. アカウントがある → 最後の操作の時刻を今に更新し、DB の名前と役割で利用者を決める。担当者から外された人は、次の要求から社員として扱われる。

[追加] アカウントの一覧の処理: 一覧の取得、役割の変更、パスワードの再設定、削除（いずれも担当者の確認を先に行う。`DS-FN-*` は `app/accounts.py`）。
- 役割の変更: 対象が無ければ「対象が無い」。担当者を外す操作で、担当者が 1 人だけなら「担当者が 0 人になる」として何もしない。
- 削除: 対象が無ければ「対象が無い」。借りている貸出があれば「借りている」として何もしない。担当者が 1 人だけで、対象がその担当者なら「担当者が 0 人になる」として何もしない。
- パスワードの再設定: 入力の検査を先に行い（画面側）、新しいハッシュで置き換える。古いパスワードは残さない。

[追加] 業務の関数の戻り値: 役割の変更・削除は結果の文字列（`ACCOUNT_OK`、`ACCOUNT_NOT_FOUND`、`ACCOUNT_LAST_MANAGER`、`ACCOUNT_BORROWING`）を返す。画面の関数はこれを文言に変える。

バッチ設計: 無し。

## 5. クラス設計

クラスは作らない。増やす関数（モジュールは既存のまま）:

- アカウント（`app/accounts.py`）: 一覧（`DS-FN-LIST-ACCOUNTS`）、利用者の 1 件の取得（`DS-FN-GET-ACCOUNT`）、役割の変更（`DS-FN-CHANGE-ACCOUNT-ROLE`）、パスワードの再設定（`DS-FN-RESET-ACCOUNT-PASSWORD`）、削除（`DS-FN-DELETE-ACCOUNT`）。
- 検査（`app/validation.py`）: パスワードの検査（`DS-FN-VALIDATE-PASSWORD`）。アカウント登録の検査（既存）も同じ規則を使う。
- 認証（`app/auth.py`）: 現在の利用者を DB から引き直す（`DS-FN-LOAD-CURRENT-USER` の変更）。引数に DB の接続を取る。
- 画面（`app/views.py`）: アカウントの一覧（`DS-FN-SHOW-ACCOUNT-LIST`）、役割の変更の送信（`DS-FN-SUBMIT-ACCOUNT-ROLE`）、パスワードの再設定の表示と送信（`DS-FN-SHOW-PASSWORD-RESET`、`DS-FN-SUBMIT-PASSWORD-RESET`）、削除の送信（`DS-FN-SUBMIT-ACCOUNT-DELETE`）。要求の前に、利用者の引き直しを `before_app_request` で行う（`app/__init__.py` の登録を、この blueprint の登録に移す）。

## 6. エラーハンドリングとセキュリティ設計

### エラーハンドリング

[追加] 担当者の操作の拒否は、既存の担当者の確認（`DS-FN-REQUIRE-MANAGER`）で行う。業務の制約（借りている社員、担当者 0 人）は業務の関数が結果を返し、画面が `.message` にする。

### 認証

[変更] 役割と存在は、要求ごとに DB から引き直す。セッションに入れた役割は信用しない（担当者から外された人が、古いセッションで担当者の操作をできないようにするため）。

### 認可

[追加] アカウントの一覧と全操作は担当者だけ（`RQ-FT-MANAGER-ONLY-ACCOUNT-MANAGEMENT`）。担当者の確認は、既存の `require_manager` を使う。

### 監査ログ

変更なし（段 1・2 と同じく、監査ログは作らない）。

### その他のセキュリティ対策

[追加] パスワードの再設定も既存と同じくハッシュ（`werkzeug.security`）で保存する。平文は残さない。

## 7. コード設計

### ディレクトリ構成

変更なし。テンプレートを 1 つ足す（`app/templates/account_list.html`、`app/templates/password_reset.html` は作らず、一覧の 1 つのテンプレートで行の展開を表す）。

### ファイル一覧（変更分）

| ファイル | 役割 | 実現する設計 ID |
|---|---|---|
| `app/accounts.py`（変更） | アカウントの登録と照合、一覧、役割の変更、パスワードの再設定、削除 | `DS-MD-ACCOUNTS`, `DS-FN-REGISTER-ACCOUNT`, `DS-FN-AUTHENTICATE-ACCOUNT`, `DS-FN-LIST-ACCOUNTS`, `DS-FN-GET-ACCOUNT`, `DS-FN-CHANGE-ACCOUNT-ROLE`, `DS-FN-RESET-ACCOUNT-PASSWORD`, `DS-FN-DELETE-ACCOUNT` |
| `app/validation.py`（変更） | 入力値の検査（パスワードの検査を追加） | `DS-MD-VALIDATION`, `DS-FN-VALIDATE-PASSWORD`（既存の検査は変更なし） |
| `app/auth.py`（変更） | 利用者の判定を DB から引き直す | `DS-MD-AUTH`, `DS-FN-LOAD-CURRENT-USER`（変更）, `DS-FN-LOGIN-USER`, `DS-FN-LOGOUT-USER`, `DS-FN-REQUIRE-MANAGER` |
| `app/views.py`（変更） | 一覧・役割・パスワード再設定・削除の画面 | `DS-MD-VIEWS`, `DS-FN-SHOW-ACCOUNT-LIST`, `DS-FN-SUBMIT-ACCOUNT-ROLE`, `DS-FN-SHOW-PASSWORD-RESET`, `DS-FN-SUBMIT-PASSWORD-RESET`, `DS-FN-SUBMIT-ACCOUNT-DELETE`, `DS-IF-ACCOUNT-LIST-SCREEN` |
| `app/__init__.py`（変更） | 利用者の引き直しの登録を blueprint に移す | `DS-MD-APP-FACTORY`, `DS-FN-CREATE-APP` |
| `app/templates/account_list.html`（新規） | アカウントの一覧の表示（テンプレートは対応表の対象外） | `DS-IF-ACCOUNT-LIST-SCREEN` |
| `app/templates/loan_status.html`（変更） | 担当者向けのリンク「アカウントの一覧」 | `DS-IF-LOAN-STATUS-SCREEN` |

テンプレートは `DS-MD-*` を付けない（段 1・2 と同じ。要素は `DS-IF-*` で受ける）。

### 対応表の粒度

`function`（段 1 のまま）。

### 依存の規則

段 1・2 のまま（`scripts/isdd/dependencies.json` は変更しない）。`app/accounts.py` は `flask`、`app/views.py`、`app/auth.py` に依存しない。新しい関数の検査は `app/validation.py` と `app/accounts.py` のどちらでも Web の枠組みを使わない。

### コーディング規約

段 1・2 のまま。

## 8. テスト設計

### 8-1. テストの種類と方針

[追加] 単体テスト（`tests/unit/`）で、新しい業務の関数（一覧、役割の変更、パスワードの再設定、削除、利用者の引き直し、パスワードの検査）の結果を確かめる。E2E（`e2e/`）は、契約の画面とシナリオを確かめる。

### 8-2. E2E テストのシナリオ（追加分）

| 設計 ID（DS-TS-*） | 対応するシナリオ（RQ-TS-*） |
|---|---|
| `DS-TS-LIST-ACCOUNTS` | `RQ-TS-LIST-ACCOUNTS` |
| `DS-TS-CHANGE-ACCOUNT-ROLE` | `RQ-TS-CHANGE-ACCOUNT-ROLE` |
| `DS-TS-KEEP-ONE-MANAGER` | `RQ-TS-KEEP-ONE-MANAGER` |
| `DS-TS-RESET-ACCOUNT-PASSWORD` | `RQ-TS-RESET-ACCOUNT-PASSWORD` |
| `DS-TS-DELETE-ACCOUNT` | `RQ-TS-DELETE-ACCOUNT` |
| `DS-TS-NO-DELETE-BORROWING-ACCOUNT` | `RQ-TS-NO-DELETE-BORROWING-ACCOUNT` |
| `DS-TS-MEMBER-AND-GUEST-CANNOT-MANAGE-ACCOUNTS` | `RQ-TS-MEMBER-AND-GUEST-CANNOT-MANAGE-ACCOUNTS` |
| `DS-TS-DEMOTED-MANAGER-LOSES-ACCESS` | `RQ-TS-DEMOTED-MANAGER-LOSES-ACCESS` |

既存の E2E（段 1・2 の場面）は、この変更の後も通す（`e2e/results/e2e.xml` に JUnit で出す）。

### 8-3. E2E の実行手段

変更なし（既存の unittest による E2E）。

### 8-4. E2E の実行コマンドと運用

変更なし。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| `DS-MD-ACCOUNTS` | `RQ-FT-LIST-ACCOUNTS`, `RQ-FT-CHANGE-ACCOUNT-ROLE`, `RQ-FT-RESET-ACCOUNT-PASSWORD`, `RQ-FT-DELETE-ACCOUNT`, `RQ-FT-KEEP-ONE-MANAGER`, `RQ-FT-NO-DELETE-BORROWING-ACCOUNT`, `RQ-DT-ACCOUNT-HARD-DELETE`, `RQ-DT-ACCOUNT-ROLE-STATE` |
| `DS-MD-VALIDATION` | `RQ-FT-RESET-ACCOUNT-PASSWORD` |
| `DS-MD-AUTH` | `RQ-FT-MANAGER-ONLY-ACCOUNT-MANAGEMENT`, `RQ-FT-ACCOUNT-CHANGE-TAKES-EFFECT`, `RQ-FT-DELETE-ACCOUNT` |
| `DS-MD-VIEWS` | `RQ-UI-ACCOUNT-LIST-SCREEN`, `RQ-FT-MANAGER-ONLY-ACCOUNT-MANAGEMENT` |
| `DS-MD-APP-FACTORY` | `RQ-FT-ACCOUNT-CHANGE-TAKES-EFFECT` |
| `DS-FN-LIST-ACCOUNTS` | `RQ-FT-LIST-ACCOUNTS` |
| `DS-FN-GET-ACCOUNT` | `RQ-FT-ACCOUNT-CHANGE-TAKES-EFFECT`, `RQ-FT-DELETE-ACCOUNT` |
| `DS-FN-CHANGE-ACCOUNT-ROLE` | `RQ-FT-CHANGE-ACCOUNT-ROLE`, `RQ-FT-KEEP-ONE-MANAGER`, `RQ-DT-ACCOUNT-ROLE-STATE` |
| `DS-FN-RESET-ACCOUNT-PASSWORD` | `RQ-FT-RESET-ACCOUNT-PASSWORD` |
| `DS-FN-DELETE-ACCOUNT` | `RQ-FT-DELETE-ACCOUNT`, `RQ-FT-KEEP-ONE-MANAGER`, `RQ-FT-NO-DELETE-BORROWING-ACCOUNT`, `RQ-DT-ACCOUNT-HARD-DELETE` |
| `DS-FN-VALIDATE-PASSWORD` | `RQ-FT-RESET-ACCOUNT-PASSWORD` |
| `DS-FN-LOAD-CURRENT-USER` | `RQ-FT-ACCOUNT-CHANGE-TAKES-EFFECT`, `RQ-FT-MANAGER-ONLY-ACCOUNT-MANAGEMENT` |
| `DS-FN-SHOW-ACCOUNT-LIST` | `RQ-FT-LIST-ACCOUNTS`, `RQ-UI-ACCOUNT-LIST-SCREEN` |
| `DS-FN-SUBMIT-ACCOUNT-ROLE` | `RQ-FT-CHANGE-ACCOUNT-ROLE`, `RQ-FT-KEEP-ONE-MANAGER` |
| `DS-FN-SHOW-PASSWORD-RESET` | `RQ-FT-RESET-ACCOUNT-PASSWORD`, `RQ-UI-ACCOUNT-LIST-SCREEN` |
| `DS-FN-SUBMIT-PASSWORD-RESET` | `RQ-FT-RESET-ACCOUNT-PASSWORD`, `RQ-FT-ACCOUNT-CHANGE-TAKES-EFFECT` |
| `DS-FN-SUBMIT-ACCOUNT-DELETE` | `RQ-FT-DELETE-ACCOUNT`, `RQ-FT-NO-DELETE-BORROWING-ACCOUNT`, `RQ-FT-KEEP-ONE-MANAGER` |
| `DS-IF-ACCOUNT-LIST-SCREEN` | `RQ-UI-ACCOUNT-LIST-SCREEN`, `RQ-FT-MANAGER-ONLY-ACCOUNT-MANAGEMENT` |
| `DS-IF-LOAN-STATUS-SCREEN` | `RQ-FT-MANAGER-ONLY-ACCOUNT-MANAGEMENT` |
| `DS-TS-LIST-ACCOUNTS` | `RQ-TS-LIST-ACCOUNTS` |
| `DS-TS-CHANGE-ACCOUNT-ROLE` | `RQ-TS-CHANGE-ACCOUNT-ROLE` |
| `DS-TS-KEEP-ONE-MANAGER` | `RQ-TS-KEEP-ONE-MANAGER` |
| `DS-TS-RESET-ACCOUNT-PASSWORD` | `RQ-TS-RESET-ACCOUNT-PASSWORD` |
| `DS-TS-DELETE-ACCOUNT` | `RQ-TS-DELETE-ACCOUNT` |
| `DS-TS-NO-DELETE-BORROWING-ACCOUNT` | `RQ-TS-NO-DELETE-BORROWING-ACCOUNT` |
| `DS-TS-MEMBER-AND-GUEST-CANNOT-MANAGE-ACCOUNTS` | `RQ-TS-MEMBER-AND-GUEST-CANNOT-MANAGE-ACCOUNTS` |
| `DS-TS-DEMOTED-MANAGER-LOSES-ACCESS` | `RQ-TS-DEMOTED-MANAGER-LOSES-ACCESS` |
| `DS-FN-REGISTER-ACCOUNT` | `RQ-FT-REGISTER-ACCOUNT`, `RQ-FT-FIRST-ACCOUNT-IS-MANAGER` |
| `DS-FN-AUTHENTICATE-ACCOUNT` | `RQ-FT-LOGIN`, `RQ-FT-LOGIN-FAILURE-NO-HINT` |
| `DS-FN-CREATE-APP` | `RQ-DT-DB-REQUIRED` |
| `DS-FN-LOGIN-USER` | `RQ-FT-LOGIN` |
| `DS-FN-LOGOUT-USER` | `RQ-FT-LOGOUT` |
| `DS-FN-REQUIRE-MANAGER` | `RQ-FT-MANAGER-ONLY-EQUIPMENT-OPERATION`, `RQ-FT-MANAGER-ONLY-ACCOUNT-MANAGEMENT` |

### 11-1. 除外要件

除外要件は無い。

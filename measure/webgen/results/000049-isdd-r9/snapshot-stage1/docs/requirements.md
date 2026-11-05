# 要件定義書: 理髪店管理ウェブサイト

- 作成日: 2026-11-05
- フロー: 新規（既存コードなし、isdd の文書なし）
- 状態: 承認済（2026-11-05。1-2 の決め事は全件承認。技術選定は未調査のままの承認）

## 1. 目的・前提

- システムの目的: 理髪店の施術スタッフ（バーバー）と施術メニューを一覧・登録できるようにし、顧客への案内を WhatsApp で送れるようにする。
- 用語集

  | 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 |
  |---|---|---|---|
  | バーバー | 施術を行う店のスタッフ | バーバーの一覧と追加 | 理髪師、スタッフ |
  | 施術メニュー | 店が提供するサービス（カット、ひげそり等） | 施術メニューの一覧と追加 | サービス |
  | 顧客 | 案内の送信先となる人。顧客の情報は本システムに保存しない | 送信画面で電話番号を入力する相手 | クライアント、client |
  | WhatsApp 送信リンク | WhatsApp を開き、メッセージを入れた状態にする URL（wa.me 形式） | 送信画面で作られ、利用者がクリックして送る | click-to-chat |

- システムの形態: GUI（ブラウザの画面）のみ。

### 1-1. 技術制約（前提として記録する。要件ではないため ID は付与しない）

| 制約項目 | 内容 | 出どころ（誰がいつ答えたか） |
|---|---|---|
| 既存コードベース | 無し（リポジトリに既存のソースコードは無い） | リポジトリの確認（2026-11-05） |
| 配備先 | 利用者の PC でローカル起動する。待ち受けは 127.0.0.1 | contract.md（`http://127.0.0.1:$PORT`） |
| チームの技術 | 未確認（扱える言語・禁止技術の回答が無い） | 未確認。質問 3 で確認 |
| ライセンスとコスト | 無料のライブラリのみ。外部サービス・有償 API は使えない。SQLite または JSON ファイルで保存可 | contract.md |
| 性能と規模の目安 | 利用人数は未確認（決め事 D18 で 1〜3 名と仮置き）。応答時間の要求は無い | 未確認。1-2 の D18 |
| 実行環境 | Python 3.12（python3）と Node.js 24（node, npm）が使える。ブラウザは Chromium | contract.md |
| 画面の言語 | 英語 | contract.md |

### 1-2. 依頼に無く自分で決めた項目（必須）

依頼と contract.md に無いことを決めた。質問 2 で承認を得る。承認前は「未確認」のまま。

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| D1 WhatsApp 送信の方法 | サーバーは WhatsApp へ通信しない。送信画面で、メッセージを入れた wa.me 送信リンクを顧客ごとに作って表示し、スタッフがリンクを開いて WhatsApp で送る。送信済みかはシステムで判定しない | 契約で外部サービス・有償 API が使えないため。依頼の「WhatsApp で通知を送る」を、この方法で満たす最小案 | 承認済（2026-11-05） |
| D2 外部連携の扱い | 外部連携は無い（サーバーから外部への通信なし）。D1 の送信リンクは利用者のブラウザが開く | D1 の結果 | 承認済（2026-11-05） |
| D3 認証・権限 | 認証（ログイン）も権限の区別も無い。画面はだれでも使える | 依頼に無い。社内 1 台での利用を想定した最小案 | 承認済（2026-11-05） |
| D4 送信先 | 顧客の一覧（顧客マスタ）は作らない。送信画面で電話番号を 1〜20 件入力する | 依頼に顧客管理は無い。最小案 | 承認済（2026-11-05） |
| D5 送信の記録 | 送信履歴は保存しない | 依頼に無い。最小案 | 承認済（2026-11-05） |
| D6 編集・削除 | バーバーと施術メニューは一覧と追加だけ。編集・削除は無い | 依頼は「追加」と「閲覧」だけ。最小案 | 承認済（2026-11-05） |
| D7 入力規則（バーバー） | 名前は必須で 1〜60 文字。専門は任意で 0〜100 文字。電話番号は任意で、空、または数字・先頭の +・空白・ハイフン・丸括弧のみの 8〜15 桁 | 依頼に規則が無い。最小案の一般的な範囲 | 承認済（2026-11-05） |
| D8 入力規則（施術メニュー） | 名前は必須で 1〜80 文字。料金は必須で 0 以上 10000 以下の数値（小数第 2 位まで）。所要時間は必須で 5〜480 の整数（分）。説明は任意で 0〜300 文字 | 依頼に規則が無い。最小案 | 承認済（2026-11-05） |
| D9 入力規則（通知） | 電話番号は 1〜20 件を改行またはカンマで区切る。各番号は D7 と同じ書式（国番号を含めること）。メッセージは必須で 1〜500 文字（改行可） | 依頼に規則が無い。wa.me は国番号付きの数字だけを受け付けるため | 承認済（2026-11-05） |
| D10 エラーの見せ方 | 英語のエラー文を、フォームの上部に項目ごとにまとめて表示する。入力値は残す。エラーがあれば保存・送信リンク作成は行わない | 依頼に無い。最小案 | 承認済（2026-11-05） |
| D11 同名の登録 | 同じ名前のバーバー、同じ名前の施術メニューの登録を許す（重複チェック無し） | 依頼に無い。最小案 | 承認済（2026-11-05） |
| D12 一覧の表示 | 件数の上限・ページ送りは無い。登録の古い順に並べる。0 件のときは「No barbers yet.」「No services yet.」を表示する | 依頼に無い。最小案 | 承認済（2026-11-05） |
| D13 通貨 | 料金は通貨記号を付けず数値だけで表示する（例: 25.00） | 通貨の回答が無い。最小案 | 承認済（2026-11-05） |
| D14 同時操作 | 1 台の PC で使う前提。同時更新の排他制御は無い（後から保存した内容が残る） | 利用人数の決め事 D18 から | 承認済（2026-11-05） |
| D15 初期データ | DATA_DIR に保存ファイルが無い（空）のとき、サンプルのバーバー 3 件と施術メニュー 4 件を入れる。保存ファイルがあれば何もしない | 依頼と contract.md（空でもサンプルで全機能を試せること） | 承認済（2026-11-05） |
| D16 色と背景 | 画面の主色は dim gray（#696969）。背景は薄い青灰色に白い雪片が上から舞う（CSS アニメーション）。OS の「動きを減らす」設定があれば雪を止める | 依頼の「snow in the background」「dim gray for the interface」をそのまま使う。動きを減らす設定への対応は最小の配慮 | 承認済（2026-11-05） |
| D17 画面の移動 | 全画面の上部に常時表示するメニュー: Home / Barbers / Services / Notify。現在の画面を示す | contract.md の「保守しやすいナビゲーション」（わかりやすさ）から | 承認済（2026-11-05） |
| D18 利用人数・性能 | 同時に 1〜3 名が使う想定。応答時間の目標は決めない | 利用人数の回答が無い。最小案 | 承認済（2026-11-05） |
| D19 起動の既定値 | PORT の既定値は 8000（contract.md）。DATA_DIR の既定値は `./data`（プロジェクト直下） | contract.md の既定値は PORT のみ。DATA_DIR の既定は最小案 | 承認済（2026-11-05） |
| D20 保存方式 | SQLite の 1 ファイル（DATA_DIR 配下）に保存する。技術選定は未調査（ユーザー承認: 2026-11-05） | contract.md が SQLite を認めている。データの量は小さい | 承認済（2026-11-05） |
| D21 業務の数値 | 現状の件数・時間は不明のまま。KPI は「不明」と書き、見込み経営効果は算定しない | 質問 4 で「分からない。任せる」 | 承認済（2026-11-05） |

## 2. 業務

- 対象業務一覧（各業務に `RQ-BZ-*` を付与）

  | RQ-BZ-ID | 業務名 | 業務の範囲 | 担当者 |
  |---|---|---|---|
  | RQ-BZ-SHOP-OPERATION | 店舗の運営 | 施術スタッフの管理、施術メニューの管理、顧客への WhatsApp 案内 | 店舗スタッフ |

- 業務フロー

  ```mermaid
  flowchart LR
      A[スタッフ情報を登録・確認] --> B[施術メニューを登録・確認]
      B --> C[顧客へ WhatsApp で案内]
  ```

### 2-1. 業務の問題（あるべき姿と現状のギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| スタッフと施術メニューを 1 か所で見られない | RQ-BZ-SHOP-OPERATION | スタッフと施術メニューを 1 画面ずつで見られる | 依頼では現状の方法が示されていない | 不明（依頼に数値なし。現状の件数・時間を質問 4 で確認） | 問い合わせへの答えに時間がかかる可能性がある（推定。未確認） |
| 顧客への案内を個別に送る手段が無い | RQ-BZ-SHOP-OPERATION | 案内文を入れて、顧客へ WhatsApp で送れる | 依頼では現状の方法が示されていない | 不明（依頼に数値なし。質問 4 で確認） | 案内の送り忘れ、文面の揺れ（推定。未確認） |

### 2-2. 業務課題一覧（必須）

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| RQ-BK-MANAGE-BARBER-ROSTER | 施術スタッフ（バーバー）の情報を一覧で管理する | スタッフと施術メニューを 1 か所で見られない | 全スタッフを一覧で確認し、追加できる（目標値は未確認） | RQ-BZ-SHOP-OPERATION |
| RQ-BK-MANAGE-SERVICE-MENU | 施術メニュー（サービス）を一覧で管理する | スタッフと施術メニューを 1 か所で見られない | 全メニューを一覧で確認し、追加できる（目標値は未確認） | RQ-BZ-SHOP-OPERATION |
| RQ-BK-NOTIFY-CLIENTS-WHATSAPP | 顧客へ WhatsApp で案内を送る | 顧客への案内を個別に送る手段が無い | 案内文から WhatsApp の送信リンクを作り、顧客ごとに送れる（目標値は未確認） | RQ-BZ-SHOP-OPERATION |

### 2-3. 見込み経営効果

見込み経営効果は算定しない（理由: 依頼に金額・件数・時間の現状値が無く、効果を数値で示せないため。質問 4 で数値が示されれば追記する）。

## 3. 機能要件

- 入力データ: 人手入力（フォーム）。外部からの入力は無い。
- 出力データ: 画面の表示。送信画面では WhatsApp 送信リンク（D1）。
- 利用者の利用フロー

  ```mermaid
  flowchart TD
      H[Home] --> BL[Barbers 一覧]
      BL -->|Add barber| BA[バーバー追加]
      BA -->|保存成功| BL
      H --> SL[Services 一覧]
      SL -->|Add service| SA[施術メニュー追加]
      SA -->|保存成功| SL
      H --> N[Notify 送信画面]
      N -->|送信リンク作成| N
      N -->|リンクを開く| W[WhatsApp]
  ```

- 業務フローとの対応: 業務フローの「スタッフ情報」は Barbers、「施術メニュー」は Services、「顧客へ案内」は Notify に対応する。

- 機能一覧

  | RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか |
  |---|---|---|---|---|
  | RQ-FT-BROWSE-BARBERS | マスタ管理 | バーバーの一覧を見る | RQ-BK-MANAGE-BARBER-ROSTER | 店のスタッフが分からない |
  | RQ-FT-ADD-BARBER | マスタ管理 | バーバーを 1 人追加する | RQ-BK-MANAGE-BARBER-ROSTER | 新しいスタッフを登録できない |
  | RQ-FT-BROWSE-SERVICES | マスタ管理 | 施術メニューの一覧を見る | RQ-BK-MANAGE-SERVICE-MENU | 提供メニューと料金が分からない |
  | RQ-FT-ADD-SERVICE | マスタ管理 | 施術メニューを 1 件追加する | RQ-BK-MANAGE-SERVICE-MENU | 新しいメニューを登録できない |
  | RQ-FT-SEND-WHATSAPP-NOTIFICATION | 業務機能 | 案内文と顧客の電話番号から、顧客ごとの WhatsApp 送信リンクを作り、開けるように表示する | RQ-BK-NOTIFY-CLIENTS-WHATSAPP | 顧客へ WhatsApp で案内を送る手段が無い |
  | RQ-FT-VALIDATE-ENTRY-FIELDS | 業務機能 | 追加・送信の入力を規則（D7〜D9）で検査し、違反があれば保存・送信を止めて理由を示す | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP | 不正な値（空の名前、0 件の番号など）が保存され、一覧や送信が壊れる |
  | RQ-FT-SEED-SAMPLE-DATA | 運用 | 保存ファイルが無いとき、サンプルのバーバーと施術メニューを入れる | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU | 空の状態では全機能を試せない（contract.md の要求） |

### 3-1. 帳票・出力ファイル

帳票・出力ファイルは無い。WhatsApp 送信リンクは画面上に表示する（RQ-UI-NOTIFY-SCREEN）。

### 3-2. 業務ルール

| RQ-ID | ルール名 | 内容（条件と結果） | 違反時・エラー時の業務上の扱い | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| RQ-FT-VALIDATE-ENTRY-FIELDS | 入力の検査 | 項目ごとの規則（D7〜D9）を満たすこと。通知は、電話番号の全件が規則を満たし、かつ案内文が規則を満たすときだけ送信リンクを作る | 違反した項目をすべてフォーム上部に英語で示し、入力値を残す。何も保存・作成しない | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP |

### 3-3. 外部連携

外部連携は無い（D2）。WhatsApp は D1 のとおり、利用者のブラウザで送信リンクを開く方式で、サーバーから外部へ接続しない。

## 4. データ

### 4-1. データ要件一覧

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| RQ-DT-LOCAL-STORAGE | 内部データ | バーバーと施術メニューを SQLite の 1 ファイル（DATA_DIR 配下の `barbershop.db`）に保存する。保持期間は無期限（削除機能が無いため）。外部 DB は無い。DB が必要な理由は、再起動後もデータを残すため。初期件数はサンプル 7 件、件数の増加は不明（D18 の規模を前提とする） | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU | 再起動のたびに登録内容が消える |

### 4-2. 業務エンティティとデータ項目

| RQ-ID | カテゴリ | 業務エンティティ名 | 対応業務課題ID（RQ-BK-*） | この業務エンティティが無いと何が困るか |
|---|---|---|---|---|
| RQ-DT-BARBER | マスタ | バーバー | RQ-BK-MANAGE-BARBER-ROSTER | スタッフの一覧ができない |
| RQ-DT-SERVICE | マスタ | 施術メニュー | RQ-BK-MANAGE-SERVICE-MENU | 施術メニューの一覧ができない |

| エンティティ名 | 項目名 | 業務上の意味 | 必須 | 形式・桁 | 値の範囲・制約 | 例 |
|---|---|---|---|---|---|---|
| バーバー | name | スタッフの名前 | 必須 | 文字列 1〜60 文字 | 空白のみは不可（D7） | Maria Lopez |
| バーバー | specialty | 得意な施術 | 任意 | 文字列 0〜100 文字 | — | Fades and beard trims |
| バーバー | phone | 連絡先の電話番号 | 任意 | 数字・+・空白・ハイフン・丸括弧、8〜15 桁 | 空でもよい（D7） | +1 555 0101 |
| 施術メニュー | name | メニューの名前 | 必須 | 文字列 1〜80 文字 | 空白のみは不可（D8） | Classic haircut |
| 施術メニュー | price | 料金（通貨記号なし） | 必須 | 数値、小数第 2 位まで | 0 以上 10000 以下（D8） | 25.00 |
| 施術メニュー | duration_min | 所要時間（分） | 必須 | 整数 | 5 以上 480 以下（D8） | 30 |
| 施術メニュー | description | メニューの説明 | 任意 | 文字列 0〜300 文字 | — | Scissor and clipper finish |

### 4-3. CRUD テーブル（必須）

| エンティティ名 | Create | Read（一覧） | Read（詳細） | 検索 | Update | Delete | 備考 |
|---|---|---|---|---|---|---|---|
| バーバー | ○ | ○ | × | × | × | × | 一覧は D12 の順。更新・削除は D6 により対象外 |
| 施術メニュー | ○ | ○ | × | × | × | × | 一覧は D12 の順。更新・削除は D6 により対象外 |

- 送信リンクは保存しないため、業務エンティティは上の 2 件だけ（D5）。
- トランザクション・同時更新が要る操作は無い（D14）。

### 4-4. 状態遷移

状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI の場合のみ）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| RQ-UI-HOME-SCREEN | Home | なし | 3 つの機能への入口を表示する | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP |
| RQ-UI-BARBER-LIST-SCREEN | Barbers（一覧） | バーバー:Read（一覧）、バーバー:Create への入口 | バーバーの一覧を表示し、Add barber への入口を置く | RQ-BK-MANAGE-BARBER-ROSTER |
| RQ-UI-BARBER-ADD-SCREEN | Add barber | バーバー:Create | 入力フォームで 1 人分を登録する | RQ-BK-MANAGE-BARBER-ROSTER |
| RQ-UI-SERVICE-LIST-SCREEN | Services（一覧） | 施術メニュー:Read（一覧）、施術メニュー:Create への入口 | 施術メニューの一覧を表示し、Add service への入口を置く | RQ-BK-MANAGE-SERVICE-MENU |
| RQ-UI-SERVICE-ADD-SCREEN | Add service | 施術メニュー:Create | 入力フォームで 1 件を登録する | RQ-BK-MANAGE-SERVICE-MENU |
| RQ-UI-NOTIFY-SCREEN | Notify | なし（保存しない） | 案内文と電話番号を入力し、顧客ごとの WhatsApp 送信リンクを表示する | RQ-BK-NOTIFY-CLIENTS-WHATSAPP |
| RQ-UI-VISUAL-THEME | 全画面（共通レイアウト） | なし | 雪の背景と dim gray の画面を全画面に適用する（D16） | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP |

画面ごとの 5 項目（画面の目的、主要要素、入力項目、表示項目、エラー時の見え方）:

- Home: 目的は機能への入口。要素は見出し、3 つのカード（Barbers、Services、Notify）。入力なし。表示はバーバー数と施術メニュー数（任意項目なし）。エラーなし。
- Barbers（一覧）: 目的は一覧。要素は「Add barber」ボタンと表。入力なし。表示は名前、専門、電話番号。0 件のとき「No barbers yet.」。エラーなし。
- Add barber: 目的は 1 人の登録。入力は name、specialty、phone。表示は保存後に Barbers へ移動。エラー時は入力値を残し、フォーム上部に英語のエラー一覧。
- Services（一覧）: 目的は一覧。要素は「Add service」ボタンと表。表示は名前、料金、所要時間、説明。0 件のとき「No services yet.」。
- Add service: 目的は 1 件の登録。入力は name、price、duration_min、description。保存後は Services へ移動。エラー時の見え方は Add barber と同じ。
- Notify: 目的は送信リンク作成。入力は phone numbers（改行またはカンマ区切り）と message。送信後は同じ画面に顧客ごとの「Open in WhatsApp」リンクを表示。エラー時は入力を残し、リンクは作らない。

## 5. 非機能要件

- 利用者の種別: 店舗スタッフ（同じ PC を使う 1〜3 名、D18）。利用者の種別・アクセス経路の詳細（社内・インターネット）は無い。配備は 127.0.0.1 のローカル（1-1）。
- 性能: 要求は無い。
- 利用人数（同時接続数）: 1〜3 名（D18、未確認）。
- 可用性: 可用性の要求は無い。
- 移行性: 移行は無い。
- セキュリティ: 認証は無い（D3）。権限制御は無い。監査証跡の改ざん防止の要求は無い。

非機能要件の `RQ-NF-*` は作らない（上の項目はすべて「要求は無い」または決め事で、確かめたいものは無い）。

## 6. 運用要件

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| RQ-OP-START-WITH-RUN-SCRIPT | 起動 | プロジェクト直下の `setup.sh` で依存を入れ、`PORT=<番号> bash run.sh` で起動する。PORT の既定は 8000、DATA_DIR の既定は `./data`。待ち受けは 127.0.0.1。前景で動き続ける | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP | 採点者や利用者がサイトを開けない |

- ログ: ログは必要ないため、ログの内容と保存期間の記述は行わない。
- 監査ログ: 要らない（D3）。
- 監視・アラート: 監視・アラートは必要ないため、監視・アラートの内容と対応方法の記述は行わない。
- バックアップと復旧: バックアップは必要ない（DATA_DIR のファイルを手でコピーする以外の手順は決めない）。

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| RQ-TS-START-WITH-SAMPLE-DATA | 空の DATA_DIR で起動すると、サンプルが見えること | DATA_DIR が空 | 起動し、Barbers と Services を開く | バーバー 3 件、施術メニュー 4 件が表示される | RQ-FT-SEED-SAMPLE-DATA, RQ-UI-BARBER-LIST-SCREEN, RQ-UI-SERVICE-LIST-SCREEN | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU |
| RQ-TS-NAVIGATE-FROM-HOME | Home からすべての機能に行けること | 起動済み | Home を開く。上部メニューと Home のカードから Barbers、Services、Notify を順に開く | 各画面が開き、メニューに現在の画面が示される | RQ-UI-HOME-SCREEN | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP |
| RQ-TS-BROWSE-AND-ADD-BARBER | バーバーを追加し、一覧で見られること | 起動済み | Add barber で name「Test Barber」、specialty「Beard」を入力して保存する | Barbers に「Test Barber」が追加される | RQ-FT-BROWSE-BARBERS, RQ-FT-ADD-BARBER, RQ-UI-BARBER-LIST-SCREEN, RQ-UI-BARBER-ADD-SCREEN | RQ-BK-MANAGE-BARBER-ROSTER |
| RQ-TS-BROWSE-AND-ADD-SERVICE | 施術メニューを追加し、一覧で見られること | 起動済み | Add service で name「Test Cut」、price「12.50」、duration_min「20」を入力して保存する | Services に「Test Cut」が料金 12.50、所要時間 20 で追加される | RQ-FT-BROWSE-SERVICES, RQ-FT-ADD-SERVICE, RQ-UI-SERVICE-LIST-SCREEN, RQ-UI-SERVICE-ADD-SCREEN | RQ-BK-MANAGE-SERVICE-MENU |
| RQ-TS-SEND-WHATSAPP-LINKS | 2 件の番号に送信リンクが作られること | 起動済み | Notify で 2 件の番号（国番号付き）と案内文を入力して送信する | 番号ごとに「Open in WhatsApp」のリンクが表示され、リンクの URL に番号と案内文（URL エンコード）が含まれる | RQ-FT-SEND-WHATSAPP-NOTIFICATION, RQ-UI-NOTIFY-SCREEN | RQ-BK-NOTIFY-CLIENTS-WHATSAPP |
| RQ-TS-REJECT-INVALID-ENTRIES | 不正な入力が保存・送信されず、理由が示されること | 起動済み | Add barber で名前を空にして保存。Add service で料金に -1 を入力。Notify で番号を 1 件だけ不正（例: abc）にして送信 | 3 画面とも保存・リンク作成は行われず、フォーム上部に英語のエラーが出て、入力値が残る | RQ-FT-VALIDATE-ENTRY-FIELDS, RQ-UI-BARBER-ADD-SCREEN, RQ-UI-SERVICE-ADD-SCREEN, RQ-UI-NOTIFY-SCREEN | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP |
| RQ-TS-SNOW-AND-GRAY-THEME | 全画面に雪の背景と dim gray が使われていること | 起動済み | 任意の画面を開き、背景と主要な色（メニュー、ボタン）を確かめる。動きを減らす設定で雪が止まることを確かめる | 背景に雪が舞い、メニューとボタンが #696969 である。動きを減らす設定では雪が止まる | RQ-UI-VISUAL-THEME | RQ-BK-MANAGE-BARBER-ROSTER, RQ-BK-MANAGE-SERVICE-MENU, RQ-BK-NOTIFY-CLIENTS-WHATSAPP |

- 全機能（3 の機能一覧、3-2、4-5）を、少なくとも 1 本のシナリオで確かめる。
- 権限制御は無いため、ロール別のシナリオは無い。同時更新は D14 のとおり対象外。

## 8. 網羅性・整合チェック

- 要件 ID の整合: `rq_integrity_checker.py` を実行する（下の実行ログ）。
- 網羅性: すべての RQ-FT・RQ-UI は、第 7 章のいずれかのシナリオに現れる（RQ-EX は無い）。
- 業務課題: 3 件すべてに機能がある。見込み経営効果は算定しない（2-3）。
- 依頼に無い画面: Home と Notify の結果表示の 2 点。Home は契約の「ナビゲーションが分かりやすいこと」を満たすため。
- 削除できる要件: 無し（すべての機能が依頼のどれかに対応する）。

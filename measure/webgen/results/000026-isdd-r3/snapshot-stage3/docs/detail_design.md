# 詳細設計書: アンケートサイト（Surveys Website）

## 1. 言語・フレームワーク・アーキテクチャの選定

- 判定日時: 2026-11-05
- 技術制約の要約（要件定義書 1-1）: 新規開発。ローカルで `bash run.sh` により直接起動する。Python 3.12 か Node.js 24。無償のものだけ。画面は英語。DATA_DIR が空でもサンプルが表示される。
- 判断軸ごとの該当有無

  | 判断軸 | 該当 | 理由 |
  |---|---|---|
  | 既存資産との整合 | 無し | 新規開発 |
  | チームの技術 | 有り | Python 3.12 か Node.js 24 のどちらか |
  | 配備先 | 有り | ローカルの `bash run.sh`。コンテナは使わない |
  | 認証と認可の境界 | 無し | ログイン・権限の区別は無い |
  | 画面の規模 | 小 | 4 画面と投票の送信 1 つ |
  | データの規模と構造 | 小 | アンケート 3 件程度。参照関係は単純。SQLite で十分 |
  | 外部連携 | 無し | 外部連携は無い |
  | ライセンスとコスト | 有り | 無償のみ。外部ライブラリは増やさない |
  | 保守性 | 有り | 依存が少ないほど保守が単純 |

- 候補の比較表

  | 候補 | 判断軸ごとの評価 | 出典 URL | 確認日 |
  |---|---|---|---|
  | A: Python 3.12 + 標準ライブラリ（http.server、sqlite3） | 依存の追加なし（setup.sh は不要な取得が無い）。画面 4 つと POST 1 つの規模に十分。E2E も標準ライブラリで書ける | 未調査（ユーザー回答による承認。ANSWERS.md「技術選定: 推奨の案でよい」） | 2026-11-05 |
  | B: Python 3.12 + Flask + SQLite | 画面は少ないが、フレームワークの追加取得が要る。setup.sh で取得が必要 | 未調査 | 2026-11-05 |
  | C: Node.js 24 + 標準ライブラリ | 候補 A と同等の規模で実装できる。ただし SQLite の標準モジュールの扱いを別途確かめる必要がある | 未調査 | 2026-11-05 |

- 最終選定結果: 言語 Python 3.12（contract.md の `python3`）、フレームワーク無し（標準ライブラリの `http.server`）、DB SQLite（標準ライブラリの `sqlite3`）、実行形態はサーバー（`bash run.sh` で前面起動）。
- 選定理由: 要件は画面 4 つと投票 1 操作の小さな規模で、依存を増やす利点が無い。標準ライブラリだけなら `setup.sh` の取得が不要で、再現しやすい。
- 注意: 公式情報の調査は、この環境の検索ツールの権限が得られず未実施。ANSWERS.md の「技術選定: 推奨の案でよい」を承認として進めた。ローカルで確認できた Python は 3.9.6 だけで、3.12 は未確認。コードは 3.9 以降で動く文法に限る。
- ユーザー承認: 2026-11-05（ANSWERS.md の固定回答による）

### フロントエンドとバックエンドを分ける構成

分けない。HTML は Python が生成し、CSS は各ページの `<style>` に書く（別ファイルは無い）。

## 2. システム構成

- コンポーネント一覧

  | コンポーネント | 役割 | 実装場所 |
  |---|---|---|
  | Web サーバー | HTTP の受付、経路の振り分け、画面の送信 | `src/web.py` |
  | 投票の業務処理 | アンケートの一覧、投票の記録、結果の集計 | `src/poll_service.py` |
  | データ保存 | SQLite の読み書き、初期データの投入 | `src/storage.py` |
  | 画面の生成 | HTML の組み立て（共通の案内メニューを含む） | `src/views.py` |
  | 起動 | DATA_DIR と PORT の読み取り、サーバーの起動 | `src/app.py` |
  | 起動スクリプト | 依存の確認、起動 | `setup.sh`、`run.sh` |

- システム全体構成図

  ```mermaid
  graph LR
      B[利用者のブラウザ] -->|HTTP 127.0.0.1| W[Web サーバー]
      W --> S[投票の業務処理]
      S --> D[データ保存]
      D --> F[(SQLite ファイル DATA_DIR/polls.db)]
      W --> V[画面の生成]
  ```

- 各コンポーネントの役割は表のとおり。
- コンポーネント間インターフェース: Web サーバーは投票の業務処理の関数を呼び、返された辞書を画面の生成に渡して HTML を返す。投票の業務処理はデータ保存の関数だけを呼ぶ。
- ネットワーク構成図: 利用者のブラウザと同じマシン上の Web サーバーとの HTTP 通信だけ（127.0.0.1）。

  ```mermaid
  graph LR
      B[ブラウザ] -->|127.0.0.1:PORT| S[Web サーバー]
  ```

## 3. データ設計

### 3-1. データモデル

DB が必要かの判定: 必要（投票を保存し、結果を集計するため）。製品は第 1 章で選んだ SQLite。

- DATA_DIR に `polls.db` を作る。DATA_DIR が無ければ作る。DATA_DIR 未指定時は `./data`（プロジェクトルート基準）。

| テーブル | カラム | 型 | 制約 |
|---|---|---|---|
| polls | id | INTEGER | 主キー、自動採番 |
| polls | question | TEXT | NOT NULL、1〜200 文字 |
| options | id | INTEGER | 主キー、自動採番 |
| options | poll_id | INTEGER | NOT NULL、polls.id への外部キー |
| options | text | TEXT | NOT NULL、1〜100 文字 |
| options | position | INTEGER | NOT NULL、poll_id 内で一意 |
| votes | id | INTEGER | 主キー、自動採番 |
| votes | option_id | INTEGER | NOT NULL、options.id への外部キー |
| votes | created_at | TEXT | NOT NULL、UTC の ISO 8601 |
| ballots | poll_id | INTEGER | NOT NULL、polls.id への外部キー。(poll_id, voter_id) の主キーの一部 |
| ballots | voter_id | TEXT | NOT NULL、32 桁の 16 進数（ブラウザ識別子）。(poll_id, voter_id) の主キーの一部 |
| ballots | created_at | TEXT | NOT NULL、UTC の ISO 8601 |

- リレーション図

  ```mermaid
  erDiagram
      POLLS ||--o{ OPTIONS : has
      OPTIONS ||--o{ VOTES : receives
      POLLS ||--o{ BALLOTS : "投票済み"
  ```

- テーブルごとの扱い: polls は `DS-SC-POLL-TABLE`、options は `DS-SC-OPTION-TABLE`、votes は `DS-SC-VOTE-TABLE`、ballots は `DS-SC-BALLOT-TABLE`、ファイル全体は `DS-SC-DATABASE-FILE` とする。
- 要件 4-2 のデータ項目とカラムの対応は、要件定義書 4-2 の表のとおり（question、text、position、created_at などの必須と桁）。

### 3-2. トランザクションと排他制御

- 投票の送信は votes への追加と ballots への追加を 1 トランザクションで行う（DS-FN-RECORD-VOTE-ONCE）。どちらかが失敗したら両方取り消す。
- 初期データ投入（polls・options・votes の追加）は 1 トランザクションで行う。途中で失敗したら全て取り消す。
- 排他制御: 同じブラウザからの同時の投票送信は、ballots の主キー (poll_id, voter_id) の一意制約で 1 件だけ記録される（DS-CL-ALREADY-VOTED-ERROR）。サーバーは 1 リクエストずつ処理するため（6 節）、同時の投票送信も直列に処理される。一意制約はその保険として残す。

### 3-3. 状態遷移

状態を持つエンティティは無い。

## 4. アーキテクチャ設計

### 4-1. 外部設計

利用者向けインターフェース（GUI。すべて英語）。配色は次の表のとおり。

#### 配色（DS-IF-COLOR-THEME）

| 対象 | 色 | 値 |
|---|---|---|
| 背景 | light yellow | `#FFFFE0` |
| 案内メニュー・見出し・ボタン・カードの枠・表の罫線・棒グラフ・通知の背景 | dark slate gray | `#2F4F4F` |
| 部品の上の文字（ボタン、案内メニューのリンク、通知） | 白 | `#FFFFFF` |
| 本文の文字 | 黒寄り | `#1A1A1A` |
| 棒グラフの地（トラック） | 淡い黄 | `#F3F0C8` |
| 無効なボタン | 灰 | `#8A9696` |

- 配色の定義は `src/views.py` の共通の CSS に 1 か所だけ置く（白と navy の背景は使わない）。

#### 投票済みの判定（ブラウザ識別子）

- ブラウザが初めて投票画面などを開くと、サーバーは 32 桁の乱数を発行して cookie `voter_id` に入れる（HttpOnly、SameSite=Lax、Path=/、有効期限 1 年）。cookie の値が 32 桁の 16 進数でなければ、新しい値を発行する（DS-FN-READ-VOTER-COOKIE）。発行したときは、その応答に Set-Cookie を付ける。
- ブラウザ識別子は利用者の区別やログインではない。cookie を消すと別のブラウザ扱いになる。


- 画面一覧

  | 画面 | 経路 | 内容 |
  |---|---|---|
  | アンケート一覧 | GET `/` | アンケート（質問、選択肢数、票の合計）を一覧。各アンケートに Vote と View results のリンク |
  | 投票画面 | GET `/surveys/<id>` | 質問と選択肢（ラジオボタン）と Submit vote ボタン。エラーがあれば上部に枠付きの文で表示。投票済みのブラウザには、選択肢と送信ボタンを無効にし「You have already voted.」と結果画面へのリンクを表示する |
  | 投票の送信 | POST `/surveys/<id>/vote`（フォーム項目 `option_id`） | 選択肢が有効で未投票なら記録して、結果画面へ 302 で移動する。無効なら投票画面を再表示する。投票済みなら記録せず、投票画面を 200 で再表示する（「You have already voted.」） |
  | アンケートの結果画面 | GET `/surveys/<id>/results` | 質問、選択肢ごとの票数、割合（小数第 1 位）、棒グラフ、票の合計。投票直後（クエリ `voted=1`）は「Your vote has been recorded.」を表示 |
  | 全体の結果画面 | GET `/results` | 全アンケートについて、選択肢ごとの票数と割合を 1 画面に並べる |

- 画面遷移図

  ```mermaid
  graph TD
      L[アンケート一覧] --> V[投票画面]
      V -->|送信（有効）| R[アンケートの結果画面]
      V -->|送信（未選択）| V
      V -->|送信（投票済み）| V
      L --> AR[全体の結果画面]
      AR --> R
      R --> V
  ```

- 案内メニュー: 全画面の上部に「Surveys」（`/`）と「Results」（`/results`）を置く。
- 画面の詳細（5 項目）
  - アンケート一覧: 目的は一覧。主要要素は見出し、一覧、リンク。表示項目は質問、選択肢数、票の合計。エラー時の見え方: アンケートが無い場合は「No surveys available.」。
  - 投票画面: 目的は投票。主要要素は質問、ラジオボタン、Submit vote ボタン。入力項目は選択肢（1 つ）。エラー時は「Please select an option.」を画面上部に表示。投票済みのときは「You have already voted.」を表示し、選択肢と送信ボタンを無効にする。
  - 結果画面（アンケート）: 目的は結果の確認。主要要素は選択肢ごとの行（名前、票数、割合、棒）と合計。
  - 全体の結果画面: 目的は全体の確認。主要要素はアンケートごとの見出しと選択肢の行。
- テンプレートと CSS は別ファイルを置かず、`src/views.py` の文字列で HTML を組み立てる。ユーザー入力と DB の文字列は HTML エスケープする。
- 外部システム連携: 無し。外部 DB 連携: 無し。

- HTTP の応答（インターフェース仕様）

  | 経路 | 入力 | 出力 | エラー仕様 |
  |---|---|---|---|
  | GET `/` | なし | 200、一覧の HTML | — |
  | GET `/surveys/<id>` | id（整数）、cookie `voter_id` | 200、投票画面（投票済みなら無効化と通知） | id が整数でない、または存在しない → 404（「Survey not found.」） |
  | POST `/surveys/<id>/vote` | option_id（整数、無い場合もある）、cookie `voter_id` | 302 で `/surveys/<id>/results?voted=1` | 投票済み → 投票を記録せず、投票画面を 200 で再表示し「You have already voted.」。option_id が無い、または整数でない、またはアンケートに属さない → 投票を記録せず、投票画面を 200 で再表示し「Please select an option.」。存在しないアンケート → 404 |
  | GET `/surveys/<id>/results` | id | 200、結果の HTML | 存在しない → 404 |
  | GET `/results` | なし | 200、全体の結果の HTML | — |
  | 上記以外の経路 | — | 404（「Page not found.」） | — |
  | 上記以外のメソッド（GET・POST 以外） | — | 501（標準ライブラリの既定の応答） | — |

- 外部システム連携: 無し。

### 4-2. 内部設計

- 処理フロー（投票の送信）

  ```mermaid
  graph TD
      A[POST を受ける] --> B{アンケートが存在するか}
      B -->|無い| N[404 を返す]
      B -->|ある| J{このブラウザは投票済みか}
      J -->|投票済み| E[投票画面を再表示する（投票済み）]
      J -->|未投票| C{選択肢 id が有効か}
      C -->|無効| G[投票画面を再表示する（未選択）]
      C -->|有効| D[投票と投票済み記録を 1 トランザクションで追加する]
      D -->|一意制約違反| E
      D -->|成功| F[結果画面へ 302 で移動する]
  ```

- 各処理の役割は 5 節の関数一覧のとおり。
- バッチ設計: 無し。

## 5. クラス設計

- クラス一覧

  | クラス | 責務（1 文） | 実装場所 |
  |---|---|---|
  | PollService | アンケートの一覧、投票の記録、結果の集計を行う | `src/poll_service.py` |
  | PollNotFoundError | 指定されたアンケートが存在しないことを表す | `src/poll_service.py` |
  | NoOptionSelectedError | 選択肢が選ばれていない、またはアンケートに属さない選択肢が送られたことを表す | `src/poll_service.py` |
| AlreadyVotedError | 同じブラウザが同じアンケートに投票済みであることを表す（票は記録されない） | `src/poll_service.py` |
  | PollRequestHandler | HTTP の 1 リクエストを経路に振り分けて応答する | `src/web.py` |

- クラス図

  ```mermaid
  classDiagram
      class PollService {
          list_polls()
          get_poll(poll_id)
          has_voted(poll_id, voter_id)
          cast_vote_once(poll_id, option_id, voter_id)
          get_poll_results(poll_id)
          get_all_results()
      }
      class PollRequestHandler {
          do_GET()
          do_POST()
      }
      PollRequestHandler ..> PollService : uses
  ```

- 主要属性: PollService は DB 接続を 1 つ持つ。PollRequestHandler は PollService を HTTP サーバーの属性として受け取る。
- メッセージ（システム内の呼び出し）と役割: 経路の振り分けが業務処理を呼び、業務処理がデータ保存を呼び、結果の辞書を画面の生成へ渡す。

## 6. エラーハンドリングとセキュリティ設計

- エラーハンドリング

  | 想定エラー | 利用者への見え方 | ログ | 処理 |
  |---|---|---|---|
  | アンケートが存在しない | 404、「Survey not found.」 | なし | 中止 |
  | 選択肢が未選択・無効 | 投票画面を再表示、「Please select an option.」 | なし | 投票を記録しない |
| 投票済みのブラウザが送信した | 投票画面を 200 で再表示、「You have already voted.」 | なし | 投票を記録しない（直接の POST も同じ） |
  | 未知の経路 | 404、「Page not found.」 | なし | 中止 |
  | 想定外の例外 | 500、「Internal server error」（平文） | 標準エラー出力 | 中止 |

- 認証: 認証は無い。
- 認可: 認可は無い（権限の区別が無い）。
- 監査ログ: 無し（運用要件で不要）。
- その他: ユーザー入力は SQL のパラメータ化で扱い、画面に出す文字列は HTML エスケープする。HTTP サーバーは 127.0.0.1 にだけ待ち受ける。ブラウザ識別子の cookie（`voter_id`）は HttpOnly・SameSite=Lax とし、32 桁の 16 進数の値だけを受け入れる。cookie は認証ではない（投票者の本人確認はしない）。

## 7. コード設計

- ディレクトリ構成

  ```
  project/
  ├── setup.sh
  ├── run.sh
  ├── src/
  │   ├── app.py
  │   ├── web.py
  │   ├── poll_service.py
  │   ├── storage.py
  │   └── views.py
  ├── tests/unit/
  └── e2e/
  ```

- ファイル一覧

  | ファイル | 役割 | 含まれる要素 | DS-MD | 実現する設計 ID |
  |---|---|---|---|---|
  | `src/app.py` | 起動の入口。環境変数の読み取り、DB の準備、サーバーの起動 | `main` | `DS-MD-APP` | `DS-FN-MAIN` |
  | `src/web.py` | HTTP の受付、経路の振り分け、ブラウザ識別子の読み書き | `PollRequestHandler`、`create_server` | `DS-MD-WEB` | `DS-CL-POLL-REQUEST-HANDLER`、`DS-FN-CREATE-SERVER`、`DS-FN-DISPATCH-GET-REQUEST`、`DS-FN-DISPATCH-POST-REQUEST`、`DS-FN-READ-VOTER-COOKIE`、`DS-IF-POLL-LIST-PAGE`、`DS-IF-POLL-VOTE-PAGE-ONE-VOTE`、`DS-IF-VOTE-SUBMIT-ONE-VOTE`、`DS-IF-POLL-RESULT-PAGE`、`DS-IF-ALL-RESULTS-PAGE` |
  | `src/poll_service.py` | 業務処理。アンケートの取得、投票、集計、投票済みの判定 | `PollService`、`PollNotFoundError`、`NoOptionSelectedError`、`AlreadyVotedError` | `DS-MD-POLL-SERVICE` | `DS-CL-POLL-SERVICE`、`DS-CL-POLL-NOT-FOUND-ERROR`、`DS-CL-NO-OPTION-SELECTED-ERROR`、`DS-CL-ALREADY-VOTED-ERROR`、`DS-FN-SERVICE-LIST-POLLS`、`DS-FN-SERVICE-GET-POLL`、`DS-FN-SERVICE-HAS-VOTED`、`DS-FN-SERVICE-CAST-VOTE-ONCE`、`DS-FN-SERVICE-GET-POLL-RESULTS`、`DS-FN-SERVICE-GET-ALL-RESULTS` |
  | `src/storage.py` | SQLite の読み書きと初期データ | `open_database`、`seed_sample_data`、`list_polls_with_totals`、`find_poll`、`list_options_with_counts`、`find_option`、`find_ballot`、`record_vote_once` | `DS-MD-STORAGE` | `DS-FN-OPEN-DATABASE`、`DS-FN-SEED-SAMPLE-DATA`、`DS-FN-LIST-POLLS-WITH-TOTALS`、`DS-FN-FIND-POLL`、`DS-FN-LIST-OPTIONS-WITH-COUNTS`、`DS-FN-FIND-OPTION`、`DS-FN-FIND-BALLOT`、`DS-FN-RECORD-VOTE-ONCE`、`DS-SC-DATABASE-FILE`、`DS-SC-POLL-TABLE`、`DS-SC-OPTION-TABLE`、`DS-SC-VOTE-TABLE`、`DS-SC-BALLOT-TABLE` |
  | `src/views.py` | HTML の組み立て（配色を含む） | `render_layout`、`render_navigation_menu`、`render_poll_list`、`render_vote_page`、`render_poll_results`、`render_all_results`、`render_not_found` | `DS-MD-VIEWS` | `DS-FN-RENDER-LAYOUT`、`DS-IF-COLOR-THEME`、`DS-IF-NAVIGATION-MENU`、`DS-FN-RENDER-POLL-LIST`、`DS-FN-RENDER-VOTE-PAGE-ONE-VOTE`、`DS-FN-RENDER-POLL-RESULTS`、`DS-FN-RENDER-ALL-RESULTS`、`DS-FN-RENDER-NOT-FOUND` |

  - 起動スクリプト（`setup.sh`、`run.sh`）と静的な HTML・CSS は対応表の対象外（運用設計の `DS-OP-START-SCRIPTS` と、画面の `DS-IF-*` の説明に含める）。
  - テストファイル（`tests/unit/`、`e2e/`）は対応表の対象外（`e2e/` は `DS-TS-*` の行だけで載せる）。

- 対応表の粒度: `function`（既定のまま。関数単位で追跡する）。
- 依存の規則

  | 依存元（ディレクトリ・ファイル） | 依存してよい先 | 依存してはいけない先 | 理由 |
  |---|---|---|---|
  | `src/app.py` | `src/web.py`、`src/storage.py`、`src/poll_service.py` | — | 起動の入口は各層を組み立てる |
  | `src/web.py` | `src/poll_service.py`、`src/views.py` | `src/storage.py` | 経路の処理は業務処理だけを通す |
  | `src/poll_service.py` | `src/storage.py` | `src/web.py`、`src/views.py`、`src/app.py` | 業務処理は HTTP と画面を知らない |
  | `src/storage.py` | — | `src/web.py`、`src/poll_service.py`、`src/views.py`、`src/app.py` | データ保存は最下層 |
  | `src/views.py` | — | `src/web.py`、`src/poll_service.py`、`src/storage.py`、`src/app.py` | 画面の生成はデータを受け取るだけ |

- コーディング規約: PEP 8 に従う。関数・クラスには日本語か英語の説明（処理・引数・戻り値）を書く。要件 ID・設計 ID はコードに書かない。対応は `docs/trace_map.md` で管理する。

## 8. テスト設計

### 8-1. テストの種類と方針

- 単体テスト: `tests/unit/` の標準ライブラリ unittest。`src/storage.py`、`src/poll_service.py`、`src/views.py` を対象にする。
- 結合テスト: `tests/unit/` に含めず、E2E テストで代える（実サーバーと SQLite の結合を確かめる）。
- 単体・結合テストの実行コマンド: `python3 -m unittest discover -s tests/unit -p "test_*.py"`
- 非機能の検証: 要件 RQ-NF-ANONYMOUS-ACCESS は `DS-TS-ANONYMOUS-ACCESS-E2E` で確かめる（実現する設計要素が無いため）。

### 8-2. E2E テストのシナリオ

要件定義書 7 章の 10 本を網羅する。

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| `DS-TS-BROWSE-POLLS-E2E` | アンケート一覧と案内メニュー | 空の DATA_DIR で起動 | `/` を開く。Surveys と Results のリンクを確認する | サンプルのアンケート 3 件とメニューが表示される |
| `DS-TS-VOTE-FOR-OPTION-E2E` | 投票と結果への反映 | 起動済み | アンケート 1 を開く。Go を選んで送信。結果画面を開く | 送信後に結果画面へ移動し、Go の票数が 1 増え、割合が表示される |
| `DS-TS-REJECT-EMPTY-VOTE-E2E` | 未選択の送信の拒否 | 起動済み | アンケート 1 を開き、選ばずに送信する | 「Please select an option.」が表示され、票の合計が変わらない |
| `DS-TS-VIEW-ALL-RESULTS-E2E` | 全体の結果画面 | 起動済み | `/results` を開く | 3 件のアンケートの選択肢ごとの票数と割合が表示される |
| `DS-TS-OPEN-UNKNOWN-POLL-E2E` | 存在しないアンケート | 起動済み | `/surveys/9999` を開く | 404 と「Survey not found.」が表示される |
| `DS-TS-ANONYMOUS-ACCESS-E2E` | ログイン無しで全画面を使える | 起動済み | 認証無しで `/`、`/surveys/1`、`/surveys/1/results`、`/results` を開く | すべて 200 で表示される |
| `DS-TS-SEED-SAMPLE-DATA-E2E` | 空の DATA_DIR で初期データが入る | DATA_DIR が空 | DATA_DIR を空にして起動し、`/` を開く | サンプルのアンケート 3 件と初期の票が表示される |
| `DS-TS-ONE-VOTE-PER-POLL-E2E` | 同じブラウザの 2 回目が数えられない | 起動済み、cookie を保持するブラウザ | アンケート 2 に Go を選んで送信。同じブラウザで投票画面を開く。同じブラウザから直接 POST する。結果画面で合計を見る | 投票画面の選択肢と送信ボタンが無効で「You have already voted.」。直接 POST の応答に「You have already voted.」。合計は 1 回目の後と同じ |
| `DS-TS-THEME-COLORS-E2E` | 全画面の配色 | 起動済み | `/`、`/surveys/1`、`/surveys/1/results`、`/results` の応答の CSS を見る | 背景 `#FFFFE0`、部品 `#2F4F4F` があり、`#000080`（navy）と白い背景が無い |
| `DS-TS-SURVEY-TERMINOLOGY-E2E` | 利用者に見える文字と URL に poll・polls が無いこと | 起動済み | `/`、`/surveys/1`、`/surveys/1/results`、`/results` の本文に poll・polls（大文字・小文字を問わない）が無いことを確かめる。`/polls/1` が 404 になることを確かめる | 4 画面に poll・polls の語が無い。`/polls/1` は 404 |

- 外部連携が無いため、モードは設けない。

### 8-3. E2E の実行手段

- 実行手段: 標準ライブラリの unittest と urllib（HTTP クライアント）で、実サーバーに対して操作する。ブラウザ自動化は使わない（ANSWERS.md の「ブラウザ自動化が使えなければ HTTP クライアントで実サーバーを確かめる形でよい」による）。
- テストは `setUpModule` で、空の一時 DATA_DIR と空いているポートを使ってサーバーを子プロセスとして起動し、`tearDownModule` でその PID だけを止める。
- ユーザー承認: 2026-11-05（ANSWERS.md による）。

### 8-4. E2E の実行コマンドと運用

- E2E の実行コマンド: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`
- テスト資産は `e2e/` に置く（`e2e/__init__.py` と `e2e/test_polls_e2e.py`）。
- 対応表の `DS-TS` 行は `e2e/test_polls_e2e.py::PollsE2ETest.<テストメソッド名>` の形で結ぶ。
- 結果は JUnit XML で `e2e/results/e2e.xml` に出す。`e2e/results/` は git 管理外（isdd-setup が `.gitignore` に足す）。
- テストが失敗したら修正と再実行を繰り返し、全件通過まで続ける。

## 9. 運用設計

- 起動方式: サーバー（コンテナは使わない）。
  - 依存の用意: `bash setup.sh`（標準ライブラリだけなので、Python 3.12 の存在確認と `DATA_DIR` の作成だけを行う）
  - 起動: `PORT=<番号> bash run.sh`。`run.sh` は `src/app.py` を前面で実行する（終了するまで戻らない）。
- 初期化: 起動時に DATA_DIR と `polls.db` が無ければ作成し、スキーマを作る（`ballots` テーブルは無ければ足す。既存の DB にも自動で足す）。アンケートが 0 件なら、サンプルのアンケートと初期の票を投入する。初期ユーザーは無い。
- 設定値・環境変数

  | 名前 | 用途 | 既定値 | 必須か |
  |---|---|---|---|
  | `PORT` | 待ち受けポート | 8000 | 不要 |
  | `DATA_DIR` | DB の保存先 | `./data` | 不要 |

- バックアップと復旧: 必要ない。
- データ移行: 移行は無い。
- 可用性: 要求は無い。
- 起動方法と操作説明は README.md に書く。

## 10. ログ・監視・アラート・障害対応設計

- ログ: ログの設計は必須ではないため、ログの種類と内容の記述は行わない（標準エラー出力に出る HTTP のアクセスログのみ）。
- 監視・アラート: 監視・アラートの設計は必須ではないため、監視・アラートの内容と対応方法の記述は行わない。
- 障害対応: DB ファイルを開けない場合は起動時に終了し、標準エラー出力にエラーを出す。利用者は起動し直す。

## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| `DS-MD-APP` | `RQ-OP-START-WITH-SCRIPTS`, `RQ-DT-SQLITE-STORAGE` |
| `DS-MD-WEB` | `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN`, `RQ-UI-ALL-RESULTS-SCREEN`, `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-OP-START-WITH-SCRIPTS`, `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-VOTED-STATE`, `RQ-NF-SURVEY-TERMINOLOGY` |
| `DS-MD-POLL-SERVICE` | `RQ-FT-LIST-POLLS`, `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-FT-SHOW-POLL-RESULTS`, `RQ-FT-SHOW-ALL-RESULTS`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-MD-STORAGE` | `RQ-DT-SQLITE-STORAGE`, `RQ-DT-SAMPLE-DATA`, `RQ-DT-POLL`, `RQ-DT-OPTION`, `RQ-DT-VOTE`, `RQ-FT-LIST-POLLS`, `RQ-FT-CAST-VOTE`, `RQ-DT-BROWSER-BALLOT`, `RQ-DT-BALLOT`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-MD-VIEWS` | `RQ-UI-NAVIGATION-MENU`, `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN`, `RQ-UI-ALL-RESULTS-SCREEN`, `RQ-FT-LIST-POLLS`, `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-FT-SHOW-POLL-RESULTS`, `RQ-FT-SHOW-ALL-RESULTS`, `RQ-UI-VOTED-STATE`, `RQ-NF-COLOR-THEME`, `RQ-NF-SURVEY-TERMINOLOGY` |
| `DS-CL-POLL-SERVICE` | `RQ-FT-LIST-POLLS`, `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-CAST-VOTE`, `RQ-FT-SHOW-POLL-RESULTS`, `RQ-FT-SHOW-ALL-RESULTS`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-CL-POLL-NOT-FOUND-ERROR` | `RQ-FT-SHOW-POLL-OPTIONS` |
| `DS-CL-NO-OPTION-SELECTED-ERROR` | `RQ-FT-REJECT-EMPTY-VOTE` |
| `DS-CL-POLL-REQUEST-HANDLER` | `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN`, `RQ-UI-ALL-RESULTS-SCREEN`, `RQ-UI-VOTED-STATE`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-FN-MAIN` | `RQ-OP-START-WITH-SCRIPTS` |
| `DS-FN-CREATE-SERVER` | `RQ-OP-START-WITH-SCRIPTS` |
| `DS-FN-DISPATCH-GET-REQUEST` | `RQ-FT-LIST-POLLS`, `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-SHOW-POLL-RESULTS`, `RQ-FT-SHOW-ALL-RESULTS` |
| `DS-FN-DISPATCH-POST-REQUEST` | `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-EMPTY-VOTE` |
| `DS-FN-OPEN-DATABASE` | `RQ-DT-SQLITE-STORAGE` |
| `DS-FN-SEED-SAMPLE-DATA` | `RQ-DT-SAMPLE-DATA` |
| `DS-FN-LIST-POLLS-WITH-TOTALS` | `RQ-FT-LIST-POLLS` |
| `DS-FN-FIND-POLL` | `RQ-FT-SHOW-POLL-OPTIONS` |
| `DS-FN-LIST-OPTIONS-WITH-COUNTS` | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-SHOW-POLL-RESULTS` |
| `DS-FN-FIND-OPTION` | `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-EMPTY-VOTE` |
| `DS-FN-SERVICE-LIST-POLLS` | `RQ-FT-LIST-POLLS` |
| `DS-FN-SERVICE-GET-POLL` | `RQ-FT-SHOW-POLL-OPTIONS` |
| `DS-FN-SERVICE-GET-POLL-RESULTS` | `RQ-FT-SHOW-POLL-RESULTS` |
| `DS-FN-SERVICE-GET-ALL-RESULTS` | `RQ-FT-SHOW-ALL-RESULTS` |
| `DS-FN-RENDER-LAYOUT` | `RQ-UI-NAVIGATION-MENU` |
| `DS-IF-NAVIGATION-MENU` | `RQ-UI-NAVIGATION-MENU` |
| `DS-FN-RENDER-POLL-LIST` | `RQ-FT-LIST-POLLS` |
| `DS-FN-RENDER-POLL-RESULTS` | `RQ-FT-SHOW-POLL-RESULTS` |
| `DS-FN-RENDER-ALL-RESULTS` | `RQ-FT-SHOW-ALL-RESULTS` |
| `DS-FN-RENDER-NOT-FOUND` | `RQ-FT-SHOW-POLL-OPTIONS` |
| `DS-IF-POLL-LIST-PAGE` | `RQ-UI-POLL-LIST-SCREEN` |
| `DS-IF-POLL-RESULT-PAGE` | `RQ-UI-POLL-RESULT-SCREEN` |
| `DS-IF-ALL-RESULTS-PAGE` | `RQ-UI-ALL-RESULTS-SCREEN` |
| `DS-SC-DATABASE-FILE` | `RQ-DT-SQLITE-STORAGE`, `RQ-DT-BROWSER-BALLOT` |
| `DS-SC-POLL-TABLE` | `RQ-DT-POLL`, `RQ-DT-SAMPLE-DATA` |
| `DS-SC-OPTION-TABLE` | `RQ-DT-OPTION` |
| `DS-SC-VOTE-TABLE` | `RQ-DT-VOTE` |
| `DS-OP-START-SCRIPTS` | `RQ-OP-START-WITH-SCRIPTS` |
| `DS-TS-BROWSE-POLLS-E2E` | `RQ-TS-BROWSE-POLLS` |
| `DS-TS-VOTE-FOR-OPTION-E2E` | `RQ-TS-VOTE-FOR-OPTION` |
| `DS-TS-REJECT-EMPTY-VOTE-E2E` | `RQ-TS-REJECT-EMPTY-VOTE` |
| `DS-TS-VIEW-ALL-RESULTS-E2E` | `RQ-TS-VIEW-ALL-RESULTS` |
| `DS-TS-OPEN-UNKNOWN-POLL-E2E` | `RQ-TS-OPEN-UNKNOWN-POLL` |
| `DS-TS-ANONYMOUS-ACCESS-E2E` | `RQ-TS-ANONYMOUS-ACCESS`, `RQ-NF-ANONYMOUS-ACCESS` |
| `DS-TS-SEED-SAMPLE-DATA-E2E` | `RQ-TS-SEED-SAMPLE-DATA` |
| `DS-SC-BALLOT-TABLE` | `RQ-DT-BROWSER-BALLOT`, `RQ-DT-BALLOT`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-FN-FIND-BALLOT` | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-VOTED-STATE` |
| `DS-FN-RECORD-VOTE-ONCE` | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-FT-CAST-VOTE`, `RQ-DT-BROWSER-BALLOT` |
| `DS-CL-ALREADY-VOTED-ERROR` | `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-FN-SERVICE-HAS-VOTED` | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-VOTED-STATE` |
| `DS-FN-SERVICE-CAST-VOTE-ONCE` | `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-FN-READ-VOTER-COOKIE` | `RQ-DT-BROWSER-BALLOT` |
| `DS-IF-POLL-VOTE-PAGE-ONE-VOTE` | `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-VOTED-STATE` |
| `DS-IF-VOTE-SUBMIT-ONE-VOTE` | `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-IF-COLOR-THEME` | `RQ-NF-COLOR-THEME` |
| `DS-FN-RENDER-VOTE-PAGE-ONE-VOTE` | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-UI-VOTED-STATE` |
| `DS-TS-ONE-VOTE-PER-POLL-E2E` | `RQ-TS-ONE-VOTE-PER-POLL` |
| `DS-TS-THEME-COLORS-E2E` | `RQ-TS-THEME-COLORS` |
| `DS-TS-SURVEY-TERMINOLOGY-E2E` | `RQ-TS-SURVEY-TERMINOLOGY`, `RQ-NF-SURVEY-TERMINOLOGY` |

### 11-1. 除外要件

除外要件は無い。

## 付録: 依頼に無く決めた項目

要件定義書 1-2 のとおり（投票の重複はアンケートごとに 1 ブラウザ 1 票、投票済みの送信は 200 で再表示、未選択は拒否、存在しないアンケートは 404、割合は小数第 1 位）。

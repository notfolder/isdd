# タスク一覧: 備品台帳と貸出状況の閲覧（段 1）

入力: `docs/detail_design.md`（設計 ID と要件 ID の対応は第 11 章）。
各タスクの完了条件を満たしてから次へ進む。テスト実行コマンドは詳細設計書 8-1 と 8-4 のものをそのまま使う。

## 0. 導入確認（固定）

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行し、対応表チェックを導入する。導入時は詳細設計書の値を渡す: 実行形態はサーバー（コンテナ無し）、認証は有り、外部連携は無し、対応表の粒度は function、依存の規則は第 7 章の表（業務の関数を Web の枠組みから独立させる規則）を `scripts/isdd/dependencies.json` に書き写す
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること

## 1. 実装（設計 ID ごと）

1. **プロジェクトの骨組みと起動スクリプト**
   - 実装する設計 ID: `DS-MD-SETUP-SCRIPT`, `DS-MD-RUN-SCRIPT`, `DS-OP-START`
   - 内容: requirements.txt（flask==3.1.3、waitress==3.0.2）、`setup.sh`（`.venv` を作り導入する）、`run.sh`（`.venv` の Python で `app` パッケージを起動する。PORT を読む）
   - 完了条件: `bash setup.sh` が成功し、`bash run.sh` が待ち受けを始めること

2. **設定の読み込み**
   - 実装する設計 ID: `DS-MD-CONFIG`, `DS-FN-LOAD-CONFIG`, `DS-OP-ENV-CONFIG`
   - 内容: PORT（既定 8000）、DATA_DIR（既定はプロジェクト直下の data。無ければ作る）、SESSION_IDLE_TIMEOUT_SECONDS（既定 1800、正の整数）を読む。不正な値は起動を止めて理由を標準エラーに出す
   - 完了条件: 単体テストで既定値と不正値の扱いが確かめられること

3. **DB の接続と初期化**
   - 実装する設計 ID: `DS-MD-DB`, `DS-FN-CONNECT-DB`, `DS-FN-INIT-SCHEMA`, `DS-SC-ACCOUNT`, `DS-SC-EQUIPMENT`
   - 内容: sqlite3 で DATA_DIR/app.db を開く。accounts と equipment のテーブルを作る（無ければ）。UNIQUE 制約を付ける。トランザクションは明示的に BEGIN IMMEDIATE で開始する
   - 完了条件: 一時ディレクトリに対して初期化を 2 回行ってもエラーにならないこと

4. **入力の検査**
   - 実装する設計 ID: `DS-MD-VALIDATION`, `DS-FN-VALIDATE-ACCOUNT-INPUT`, `DS-FN-VALIDATE-EQUIPMENT-INPUT`
   - 内容: 社員番号（6 桁の数字）、名前（空でない、30 文字以内）、パスワード（8 文字以上）、管理番号（半角の英数字とハイフン、20 文字以内、空は形式の文言）、備品名（空でない、50 文字以内）。入力欄ごとのエラー文言は契約の文言と完全一致させる。備品名の空の文言は「備品名を入力してください」
   - 完了条件: 単体テストで各境界（5/6/7 桁、29/30/31 文字、7/8 文字、20/21 文字、50/51 文字、全角）が確かめられること

5. **アカウント**
   - 実装する設計 ID: `DS-MD-ACCOUNTS`, `DS-FN-REGISTER-ACCOUNT`, `DS-FN-AUTHENTICATE-ACCOUNT`
   - 内容: 登録は BEGIN IMMEDIATE のトランザクションで、件数が 0 なら担当者、それ以外は社員として保存する。社員番号の重複は確認して返す。パスワードは Werkzeug のハッシュで保存する。照合は社員番号で行を引き、一致しなければ失敗を返す（どちらが違うかは返さない）
   - 完了条件: 単体テストで、最初の登録が担当者、2 件目が社員、重複の拒否、照合の成否が確かめられること

6. **備品**
   - 実装する設計 ID: `DS-MD-EQUIPMENT`, `DS-FN-LIST-EQUIPMENT`, `DS-FN-GET-EQUIPMENT`, `DS-FN-CREATE-EQUIPMENT`, `DS-FN-UPDATE-EQUIPMENT`, `DS-FN-DELETE-EQUIPMENT`
   - 内容: 一覧は管理番号の昇順、状態は常に「空き」、借りている社員の名前と貸出日は空。登録と修正は UNIQUE 制約の違反を重複の文言として扱う。修正の重複確認は自分を除く（UNIQUE 制約で足りる）。削除は物理削除
   - 完了条件: 単体テストで一覧の順序、登録・修正の重複、削除後に残らないことが確かめられること

7. **認証（セッション）**
   - 実装する設計 ID: `DS-MD-AUTH`, `DS-FN-LOGIN-USER`, `DS-FN-LOGOUT-USER`, `DS-FN-LOAD-CURRENT-USER`, `DS-FN-REQUIRE-MANAGER`, `DS-OP-SECRET-KEY`
   - 内容: 秘密鍵は DATA_DIR に無ければ作る（乱数 32 バイト、権限 0600）。セッションには利用者の ID と最後の操作時刻を入れる。現在の利用者の判定で、制限時間を超えていればセッションを消す。判定のたびに最後の操作時刻を更新する。担当者の確認は、担当者でなければ拒否を返す
   - 完了条件: 単体テストと、制限時間 2 秒の設定での手動確認で、超過後に未ログインになること

8. **アプリの生成とサーバー**
   - 実装する設計 ID: `DS-MD-APP-FACTORY`, `DS-FN-CREATE-APP`, `DS-MD-SERVER`, `DS-OP-SERVER-THREADS`
   - 内容: create_app で設定の読み込み、DB の初期化、秘密鍵の準備、画面の登録を行う。`app/__main__.py` は waitress を 8 スレッドで、全インターフェースの PORT で起動する
   - 完了条件: `bash run.sh` で起動し、`/` が応答すること

9. **画面と templates**
   - 実装する設計 ID: `DS-MD-VIEWS`, `DS-FN-SHOW-LOAN-STATUS`, `DS-FN-SUBMIT-ACCOUNT-REGISTER`, `DS-FN-SUBMIT-LOGIN`, `DS-FN-SUBMIT-LOGOUT`, `DS-FN-SHOW-EQUIPMENT-FORM`, `DS-FN-SUBMIT-EQUIPMENT-FORM`, `DS-FN-SUBMIT-EQUIPMENT-DELETE`, `DS-MD-TPL-BASE`, `DS-MD-TPL-LOAN-STATUS`, `DS-MD-TPL-ACCOUNT-REGISTER`, `DS-MD-TPL-LOGIN`, `DS-MD-TPL-EQUIPMENT-FORM`, `DS-IF-LOAN-STATUS-SCREEN`, `DS-IF-ACCOUNT-REGISTER-SCREEN`, `DS-IF-LOGIN-SCREEN`, `DS-IF-EQUIPMENT-FORM-SCREEN`
   - 内容: 契約のパス（`/`、`/accounts/register/`、`/login/`、`/equipment/new/`、修正は `/equipment/<管理番号>/edit/`、削除は `/equipment/<管理番号>/delete/`、`/logout/`）、入力欄の id、ボタンとリンクの文言、`.field` / `.field-error` / `.error` / `.message` / `.current-user`、`tbody tr` と `data-equipment-number` を契約どおりに出す。削除ボタンは `window.confirm` を通す。担当者以外と未ログインの要求は、設計の拒否の規則どおりに扱う。パスワードは入力欄に再表示しない
   - 完了条件: 4 画面が GET で応答し、契約の要素が出ること

10. **単体テスト**
    - 実装する設計 ID: なし（8-1 の単体テスト。対応表の粒度は関数のため、テストファイルは対応表に載せない）
    - 内容: `tests/unit/` に、タスク 2〜7 の関数の単体テストを書く
    - 完了条件: `.venv/bin/python -m unittest discover -s tests/unit` が全件通ること

11. **E2E テスト**
    - 実装する設計 ID: `DS-TS-REGISTER-FIRST-ACCOUNT`, `DS-TS-REGISTER-SECOND-ACCOUNT-AS-MEMBER`, `DS-TS-REGISTER-ACCOUNT-VALIDATION`, `DS-TS-LOGIN-AND-LOGOUT`, `DS-TS-LOGIN-FAILURE-NO-HINT`, `DS-TS-AUTO-LOGOUT-AFTER-IDLE`, `DS-TS-MANAGER-REGISTER-EQUIPMENT`, `DS-TS-EQUIPMENT-VALIDATION`, `DS-TS-MANAGER-EDIT-EQUIPMENT`, `DS-TS-MANAGER-DELETE-EQUIPMENT`, `DS-TS-MEMBER-CANNOT-OPERATE-EQUIPMENT`, `DS-TS-GUEST-CANNOT-OPERATE-EQUIPMENT`, `DS-TS-VIEW-LOAN-STATUS-AS-GUEST`, `DS-TS-VIEW-EMPTY-LOAN-STATUS`, `DS-TS-ROLE-BUTTON-VISIBILITY`, `DS-TS-LIST-RESPONSE-TIME`
    - 内容: `e2e/` に、詳細設計書 8-2 の各シナリオを 1 つの unittest のテスト関数として書く（関数名は `test_` で始め、設計 ID を小文字・アンダースコアに変えた名前にする）。一時 DATA_DIR と空いたポートでサーバーを起動し、HTTP で確かめる。制限時間のシナリオは SESSION_IDLE_TIMEOUT_SECONDS=2 で別のサーバーを起動する。応答時間のシナリオは 500 件の備品を登録してから測る
    - 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` が全件通ること

12. **導入手順（README）**
    - 実装する設計 ID: `DS-OP-FIRST-ACCOUNT-SETUP`
    - 内容: README.md に起動方法（setup.sh、run.sh、環境変数）と、最初のアカウントは担当者が登録してから社員に URL を知らせる手順を書く
    - 完了条件: README.md だけを読んで初回起動と最初のアカウント登録ができること

## 2. 実装完了確認（固定）

1. **対応表（docs/trace_map.md）更新タスク**
   - 実装したファイル・関数を `docs/trace_map.md` に登録する（function の粒度）。`DS-TS-*` は `e2e/` のテスト関数に結ぶ
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること

2. **起動確認タスク**
   - 詳細設計書 9 章の方法で `bash setup.sh` と `bash run.sh` を実行し、`/` が応答すること
   - 完了条件: 起動がエラーなく完了すること

3. **単体テスト・結合テスト全件通過タスク**
   - `.venv/bin/python -m unittest discover -s tests/unit` を実行する
   - 完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返す

4. **E2E テスト全件通過タスク**
   - `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` を実行する
   - 完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返し、全件通過まで続ける

5. **README.md 記載タスク**
   - 起動方法と初期の手順（タスク 12）が README.md にあること
   - 完了条件: README.md を読むだけで初回起動と最初のアカウント登録ができること

6. **実装完了チェックタスク**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する
   - 完了条件: 全項目が OK であること

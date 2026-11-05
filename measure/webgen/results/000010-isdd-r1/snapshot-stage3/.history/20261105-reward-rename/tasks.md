# 実装タスク: prize（景品）→ reward（報酬）の用語変更

- 入力: `change_requirements.md`、`change_detail_design.md`（`docs/active_change` が指す変更）
- 正本は書き換えない（実装後レビューで反映する）
- コードに要件 ID・設計 ID を書かない

## 1. 画面（public/）

- `public/index.html`:
  - 上部メニュー: 「Reward List」、リンク先 `#/rewards`（DS-IF-NAVIGATION-MENU）
  - `aria-label` 「Reward wheel」（DS-IF-SPIN-SCREEN-NAME-REQUIRED）
  - 報酬一覧の見出し「Reward List」と説明文（DS-IF-PRIZE-LIST-SCREEN）、表の見出し「Reward」
  - 当選記録の表の見出し「Player」「Reward」「Won at」（DS-IF-MY-WINNINGS-SCREEN-DETAILS）
- `public/app.js`: 経路の対応 `/rewards` → 報酬一覧の画面（DS-IF-NAVIGATION-MENU、4-2）。表示語の変更は無い（既存の文言は index.html 側）
- 完了条件: `grep -i prize public/index.html` が 0 件

## 2. サーバー（src/）

- `src/spin.js`: 景品 0 件のエラー文言を「No rewards are available.」（DS-IF-API-SPIN、6）。関数名・状態名は据え置く
- `src/db.js`: 初期景品の名前「Grand Prize Headphones」→「Grand Reward Headphones」（4-2 初期データ）
- 完了条件: `grep -n "No prizes\|Grand Prize" src/*.js` が 0 件

## 3. テスト（e2e/・tests/）

- `e2e/navigate-screens.test.js`: メニューのリンク名「Reward List」、リンク先 `#/rewards` に合わせる
- `e2e/view-prizes.test.js`: 見出し「Reward List」に合わせる
- `e2e/winning-details.test.js`: 表の見出し「Reward」に合わせる
- `e2e/reward-wording.test.js`（新規、DS-TS-REWARD-WORDING-E2E）: GET / の HTML に prize の語（大文字小文字を問わず）が無いこと。メニューの「Reward List」と `#/rewards` があること
- 完了条件: `node --test tests/unit/` と `mkdir -p e2e/results && node --test --test-reporter=junit --test-reporter-destination=e2e/results/e2e.xml 'e2e/*.test.js'` が全件通過

## 4. 対応表

- `docs/trace_map.md`: `DS-TS-REWARD-WORDING-E2E` → `e2e/reward-wording.test.js` の行を足す（E2E の行）
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0・警告 0（先に 3 のテストを回して `e2e/results/e2e.xml` を出す）

## 5. 文書

- `README.md`: 「prize」の語を「reward」に（画面の説明、メニュー名、初期データの説明）。`package.json` の description も同じ語にする

## 6. 実装完了の確認

1. 上の完了条件をすべて満たす
2. `PORT=任意 bash run.sh` で 3 画面（`/`、`#/rewards`、`#/winnings`）の HTML と `/app.js`、`/style.css` が取れる。HTML に prize の語が無いことを確かめる。確認後、起動したプロセスを PID で止める
3. 報告の前に、Chrome（ヘッドレス）で 3 画面のスクリーンショットを撮り、目で見える語と色を確かめる（作業の確認用。成果物にはしない）

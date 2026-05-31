# isdd tasks.md 作成ルール

isdd 詳細設計スキル（isdd-design、isdd-change-design）で生成する `tasks.md` の標準作成ルール。

---

## tasks.md の配置先

- isdd-design：`docs/detail_design.md` 保存後、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を作成
- isdd-change-design：`change_detail_design.md` 保存後、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を作成

---

## 必須記載項目

### 全タスクの網羅

- すべての実装タスクを漏れなく記載する

### タスクの完了条件

- 各タスクに完了条件を **必ず定義する**

### バリデーション

- 各タスクにバリデーションタスクを **必ず含める**

### 全体確認

- 最終的に全変更点を実装済みか確認するタスクを **必ず含める**

### 実装完了確認の必須固定タスク

以下の3タスクを**全 tasks.md の末尾（isdd-change-design 固有タスクより前）に必ず含める**。

1. **docker compose 起動確認タスク**
   - `docker-compose.yml` が存在し、`docker compose up` で全サービスが起動することを確認する
   - 完了条件: 全サービスが起動ログを出力し、エラーなく立ち上がること

2. **E2E テスト全件通過タスク**
   - `e2e/` 配下のテストを mock モードで全件実行し、全件通過を確認する
   - 実行コマンド例: `docker compose run --rm test_playwright sh -c "npm install && npx playwright test"`
   - 完了条件: テスト結果に FAIL が0件であること。失敗した場合は修正と再実行を繰り返し全件通過まで継続する

3. **README.md 起動方法・初期ユーザー記載タスク**
   - README.md に「起動方法」セクションと「初期ユーザー」情報を記載する
   - 完了条件: README.md を読むだけで初回起動から初期ログインまで完結できること

---

## isdd-change-design 固有の記載

isdd-change-design のみ、以下を **tasks.md 最後に追加する**：

- 上記タスクの次に、**変更要件定義書と変更設計書の内容を既存の `docs/requirements.md` と `docs/detail_design.md` に反映するタスクを必ず明記する**
  - このタスクには「既存ファイルが上書きされる」ことを明記する
  - 反映内容の完全性を確認する条件を定める

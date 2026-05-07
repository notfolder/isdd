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

---

## isdd-change-design 固有の記載

isdd-change-design のみ、以下を **tasks.md 最後に追加する**：

- 上記タスクの次に、**変更要件定義書と変更設計書の内容を既存の `docs/requirements.md` と `docs/detail_design.md` に反映するタスクを必ず明記する**
  - このタスクには「既存ファイルが上書きされる」ことを明記する
  - 反映内容の完全性を確認する条件を定める

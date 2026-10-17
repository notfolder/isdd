# isdd tasks.md 作成ルール

isdd 詳細設計スキル（isdd-design、isdd-change-design）で生成する `tasks.md` の標準作成ルール。

---

## tasks.md の配置先

- isdd-design：`docs/detail_design.md` 保存後、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を作成
- isdd-change-design：`change_detail_design.md` 保存と正本への反映の後、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を作成

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

### 実装開始前の必須固定タスク

以下を**全 tasks.md の先頭に必ず含める**。

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が存在しなければ `isdd-setup` スキルを実行して対応表チェックを導入する。導入時は詳細設計書の実行形態・認証の有無・外部連携の有無を `isdd-setup` に渡す
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること

isdd-change-design のみ、続けて次を含める。

0-2. **正本反映の確認タスク**
   - `isdd-change-design` が変更要件定義書と変更設計書を `docs/requirements.md` と `docs/detail_design.md` に反映済みであることを確認する。変更要件の全 [追加] RQ-ID と変更設計の全 [追加] DS-ID が正本にあり、[削除] の ID が正本に無いこと
   - 完了条件: `rq_integrity_checker.py docs/requirements.md` と `rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が合格すること。未反映があれば実装を始めず `isdd-change-design` に戻る

### 実装完了確認の必須固定タスク

以下を**全 tasks.md の末尾に必ず含める**。条件付きのタスクは、条件に当たらない場合「対象外（理由）」と書いて残す。

1. **対応表（docs/trace_map.md）更新タスク**
   - 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（`.agents/skills/isdd-common/references/trace-map-rules.md`）
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること

2. **起動確認タスク**（詳細設計書 第 1 章の実行形態に従う）
   - 実行形態がコンテナ: `docker-compose.yml`（または `compose.yaml`）が存在し、`docker compose up` で全サービスが起動することを確認する
   - 実行形態が CLI・サーバー・デスクトップ・ライブラリ: 詳細設計書 第 9 章の起動方法（またはインストール・利用手順）どおりに起動または実行できることを確認する
   - 完了条件: 起動または実行がエラーなく完了すること

3. **E2E テスト全件通過タスク**
   - `e2e/` 配下のテストを全件実行し、全件通過を確認する。外部連携がある場合は mock モードで実行する
   - 実行コマンドは詳細設計書 第 11 章に明記したものを使う
   - 完了条件: テスト結果に FAIL が 0 件であること。失敗した場合は修正と再実行を繰り返し全件通過まで継続する

4. **README.md 記載タスク**
   - README.md に「起動方法」セクションを記載する。認証がある場合は「初期ユーザー」情報も記載する
   - 完了条件: README.md を読むだけで初回起動（認証がある場合は初期ログインまで）が完結できること

5. **実装完了チェックタスク**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する
   - 完了条件: 全項目が OK であること

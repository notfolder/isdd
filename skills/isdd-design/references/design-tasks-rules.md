# isdd tasks.md 作成ルール

詳細設計スキル（isdd-design、isdd-change-design）が作る `tasks.md` のルール。実装スキル（isdd-traceable-coding）はこの tasks.md を上から順に実行する。

---

## tasks.md の配置先

- isdd-design：`docs/detail_design.md` 保存後、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を作成
- isdd-change-design：`change_detail_design.md` 保存と正本への反映の後、`.history/[YYYYMMDD]-[タスク名]/tasks.md` を作成

---

## 必須記載項目

- すべての実装タスクを書く
- 各タスクに、実装する設計 ID を書く。実装スキルが対応表（`docs/trace_map.md`）に登録する行の手がかりになり、登録漏れを防ぐため
- 各タスクに完了条件と、それを確かめる検証の手順を書く。完了条件が無いと、実装スキルが完了を判断できないため
- 最後に、すべての変更点を実装したかを確認するタスクを置く

### 実装開始前の必須固定タスク

次のタスクを tasks.md の先頭に置く。

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が存在しなければ `isdd-setup` スキルを実行して対応表チェックを導入する。導入時は詳細設計書の実行形態・認証の有無・外部連携の有無を `isdd-setup` に渡す
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること

isdd-change-design のみ、続けて次を含める。

0-2. **正本反映の確認タスク**
   - `isdd-change-design` が変更要件定義書と変更設計書を `docs/requirements.md` と `docs/detail_design.md` に反映済みであることを確認する。変更要件の全 [追加] RQ-ID と変更設計の全 [追加] DS-ID が正本にあり、[削除] の ID が正本に無いこと
   - 完了条件: `rq_ds_link_checker.py docs/requirements.md docs/detail_design.md`（isdd-traceable-coding に同梱）が合格すること。未反映があれば実装を始めず `isdd-change-design` に戻る

### 実装完了確認の必須固定タスク

次のタスクを tasks.md の末尾に置く。条件付きのタスクは、条件に当たらない場合も「対象外（理由）」と書いて残す（確認漏れと区別するため）。

1. **対応表（docs/trace_map.md）更新タスク**
   - 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（書式は trace-map-rules.md）
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること

2. **起動確認タスク**（詳細設計書 第 1 章の実行形態に従う）
   - 実行形態がコンテナ: `docker-compose.yml`（または `compose.yaml`）が存在し、`docker compose up` で全サービスが起動することを確認する
   - 実行形態が CLI・サーバー・デスクトップ・ライブラリ: 詳細設計書 第 9 章の起動方法（またはインストール・利用手順）どおりに起動または実行できることを確認する
   - 完了条件: 起動または実行がエラーなく完了すること

3. **単体テスト・結合テスト全件通過タスク**
   - 詳細設計書 8-1 の実行コマンドで単体テストと結合テストを全件実行する
   - 完了条件: テスト結果に FAIL が 0 件であること。失敗した場合は修正と再実行を繰り返す

4. **E2E テスト全件通過タスク**
   - `e2e/` 配下のテストを全件実行し、全件通過を確認する。外部連携がある場合は mock モードで実行する
   - 実行コマンドは詳細設計書 8-4 に書いたものを使う
   - 完了条件: テスト結果に FAIL が 0 件であること。失敗した場合は修正と再実行を繰り返し全件通過まで継続する

5. **README.md 記載タスク**
   - README.md に「起動方法」セクションを記載する。認証がある場合は「初期ユーザー」情報も記載する
   - 完了条件: README.md を読むだけで初回起動（認証がある場合は初期ログインまで）が完結できること

6. **実装完了チェックタスク**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する
   - 完了条件: 全項目が OK であること

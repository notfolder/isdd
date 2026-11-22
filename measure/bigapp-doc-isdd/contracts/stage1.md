# 採点の契約（総務システム）

採点は、この契約に沿って自動で行う。契約を守らないと、機能が正しくても採点で落ちる。
ここに書くのは、採点が使う接点だけ。

## 起動と確認の接点（変えないこと）

- 採点は `app.create_app({"TESTING": True, "DATABASE": <ファイルのパス>})` でアプリを作り、Flask のテスト用クライアントで操作する。`create_app` の引数と、この 2 つの設定の意味を変えない。
- 環境変数 `APP_TODAY`（`YYYY-MM-DD`）があれば、それを今日の日付として扱う（`app.core.clock.today()`）。
- 新しいデータベースには、総務の担当者が 1 人だけ入っている（社員番号 `900001`、パスワード `adminpass`）。
- `bash setup.sh` で `.venv` に依存（Flask と pytest）が入る。外部のサービスや有償のものを使わない。
- 今ある URL、入力欄の名前、`status.json` の形、HTTP の返し方（受け付けないときは 400、成功したら 302。社員の登録だけは成功で 201）を変えない。機能ごとの URL と入力欄は、`docs/module-guide.md` と各機能のコードにあるとおり。
- 社員の登録は `POST /employees/new`（`employee_no`、`name`、`role`、`dept`）、退職は `POST /employees/retire`（`employee_no`）、一覧は `GET /employees.json`、操作の記録は `GET /audit.json`。

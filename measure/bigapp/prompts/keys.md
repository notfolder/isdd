# 依頼: 総務システムに機能「鍵の貸出」（slug: `keys`）を 1 つ足す

あなたの作業フォルダは `/Users/notfolder/isdd-measure-work/bigapp-gen/keys` 。この中だけを変更する。ほかの場所のファイルは変えない。git の操作はしない。
作業フォルダには総務システムの土台（`app/core/`、`tests/conftest.py`、`docs/`）が入っている。**土台のファイルは変更しない**（`app/core/`、`app/__init__.py`、`tests/conftest.py`、`tests/test_core.py`、`docs/`、`requirements.txt`、`run.sh`、`setup.sh`、`wsgi.py`）。
まず `docs/module-guide.md`、`docs/soumu-rules.md`、`app/__init__.py`、`app/core/` の全ファイル、`tests/conftest.py` を読むこと。

作るもの:
- `app/modules/keys/`（パッケージ。テンプレートは `app/modules/keys/templates/keys/`）
- `tests/test_keys.py`（下の「きまり」を 1 つずつ確かめるテストを 12 本以上。境界の値も確かめる）

テストの実行: 作業フォルダで `/Users/notfolder/Documents/isdd/measure/bigapp/seed/.venv/bin/python -m pytest -q` を実行し、`tests/test_core.py` と `tests/test_keys.py` が全部通ること。

## 画面と URL（この形を守る。採点は別のテストがこの URL と入力欄の名前で行う）

共通:
- データを変える操作（POST）は総務の担当者（`staff_required`）だけができる。
- 受け付けないときは HTTP 400 を返し、理由を `<p class="error">…</p>` に出す。データは変えない。
- 成功したら `/keys/` へリダイレクト（302）する。
- データを変える操作は `app.core.audit.record("keys", <操作名>, <対象>)` で 1 行残す（操作名は下の表のとおり）。
- 日付の判定は必ず `app.core.clock.today()` を使う。
- 社員は `employees` テーブルから読む。対象にできるのは在籍している社員だけ（退職した社員と、存在しない社員番号は 400）。

### 貸出の機能

きまり: 貸出の期間は 1 日（返却の期限 = 貸出日 + 1 日）。1 人が同時に借りられるのは 2 件まで。返却の期限を過ぎた（今日 > 期限）貸出をこの機能で持っている社員には、新しく貸さない。貸出中の物は貸せない。貸出日は省略すると今日で、未来の日付は受け付けない。貸出中の物は削除できない。物の番号（code）は重複不可。

| URL | 入力欄 | 中身 | 操作名 |
|---|---|---|---|
| `GET /keys/` | `q`（任意。番号か名前の一部で絞り込む） | 一覧の画面（番号、名前、状態、借りている社員、貸出日、期限）と、登録・貸出・返却のフォーム | — |
| `POST /keys/items/new` | `code`、`name` | 物を登録する | `item_create` |
| `POST /keys/items/edit` | `code`、`name` | 名前を直す | `item_update` |
| `POST /keys/items/delete` | `code` | 物を削除する | `item_delete` |
| `POST /keys/lend` | `item_code`、`employee_no`、`lent_on`（任意、`YYYY-MM-DD`） | 貸し出す | `lend` |
| `POST /keys/return` | `item_code` | 返却する（貸出の記録は履歴に残す） | `return` |
| `GET /keys/history` | — | 過去の貸出の一覧の画面（新しい順） | — |
| `GET /keys/status.json` | — | 下の形の JSON（ログインしていれば誰でも見られる） | — |

`status.json` の形: `{"items": [{"code": "A-1", "name": "…", "status": "free"|"lent"|"overdue", "borrower": "100001"|null, "lent_on": "2026-06-01"|null, "due_on": "2026-06-15"|null}]}`（code の昇順。`overdue` は今日 > 期限のとき）。


## 書き方の指定（必ず守る。この機能はこの書き方で作る）

- ファイルの分け方: `web.py`（画面）と `domain.py`（判定。例外を投げて画面側で受ける）に分ける
- 期限を過ぎたかどうかは、貸出の行を読むときに SQL の CASE 式で `state` の列として作り、Python 側ではその列の値を見るだけにする
- 在籍の判定は、退職した状態の集合（`EXCLUDED_STATUSES = {'retired'}` のような定数）に入っていないかで書く
- コメントと docstring は日本語で、普通の業務システムとして自然な量にする。
- ほかの機能と共通の関数を `app/core/` に足さない。判定はこの機能の中に書く。
- 画面は実務で使える程度に作る（一覧の表、登録や操作のフォーム、エラーの表示）。CSS は `base.html` のものだけでよい。

## 終わったら

日本語で 5 行以内で報告する: 作ったファイルと行数、テストの本数と結果、書き方の指定をどう実装したか（延滞・在籍・金額・時間の単位の判定を書いた場所の `ファイル:関数名`）。
